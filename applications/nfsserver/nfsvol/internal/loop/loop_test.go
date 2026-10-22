package loop

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"sync"
	"testing"

	"golang.org/x/sys/unix"
)

// fakeAttach replaces attachFree with fn for the duration of the test.
func fakeAttach(t *testing.T, fn func(*os.File) (string, error)) {
	t.Helper()
	old := attachFree
	attachFree = fn
	t.Cleanup(func() { attachFree = old })
}

// failingAttach fails with errs in turn, then succeeds; it returns the call count.
func failingAttach(t *testing.T, errs ...error) *int {
	t.Helper()
	calls := 0
	fakeAttach(t, func(*os.File) (string, error) {
		calls++
		if calls <= len(errs) {
			return "", fmt.Errorf("LOOP_SET_FD on /dev/loop7: %w", errs[calls-1])
		}
		return "/dev/loop7", nil
	})
	return &calls
}

func backingFile(t *testing.T) string {
	t.Helper()
	path := filepath.Join(t.TempDir(), "osb2-workspace-1-pvc-0000.quota")
	if err := os.WriteFile(path, nil, 0644); err != nil {
		t.Fatal(err)
	}
	return path
}

func TestAttachRetriesWhenDeviceIsTaken(t *testing.T) {
	calls := failingAttach(t, unix.EBUSY, unix.ENXIO, unix.EBUSY)
	got, err := Attach(backingFile(t))
	if err != nil {
		t.Fatalf("Attach: %v", err)
	}
	if got != "/dev/loop7" || *calls != 4 {
		t.Errorf("Attach = %q after %d calls, want /dev/loop7 after 4", got, *calls)
	}
}

func TestAttachGivesUpAfterRetries(t *testing.T) {
	errs := make([]error, attachRetries+5)
	for i := range errs {
		errs[i] = unix.EBUSY
	}
	calls := failingAttach(t, errs...)
	if _, err := Attach(backingFile(t)); !errors.Is(err, unix.EBUSY) {
		t.Fatalf("Attach error = %v, want EBUSY", err)
	}
	if *calls != attachRetries+1 {
		t.Errorf("Attach made %d attempts, want %d", *calls, attachRetries+1)
	}
}

func TestAttachDoesNotRetryOtherErrors(t *testing.T) {
	calls := failingAttach(t, unix.EINVAL)
	if _, err := Attach(backingFile(t)); !errors.Is(err, unix.EINVAL) {
		t.Fatalf("Attach error = %v, want EINVAL", err)
	}
	if *calls != 1 {
		t.Errorf("Attach made %d attempts, want 1", *calls)
	}
}

// mount-all and the watchdog attach from 32 workers at once. LOOP_CTL_GET_FREE
// hands every caller the same lowest unbound device until one binds it, so the
// others' LOOP_SET_FD failed with EBUSY ("LOOP_SET_FD on /dev/loop2549: device
// or resource busy" on osb2). The fake models exactly that.
func TestConcurrentAttachesAllSucceed(t *testing.T) {
	var mu sync.Mutex
	bound := map[int]bool{}
	fakeAttach(t, func(*os.File) (string, error) {
		mu.Lock()
		n := 0
		for bound[n] { // GetFree: lowest unbound device, not reserved
			n++
		}
		mu.Unlock()
		runtime.Gosched()
		mu.Lock()
		defer mu.Unlock()
		if bound[n] {
			return "", fmt.Errorf("LOOP_SET_FD on %s: %w", DevPath(n), unix.EBUSY)
		}
		bound[n] = true
		return DevPath(n), nil
	})

	const workers = 32
	backing := backingFile(t)
	devices := make([]string, workers)
	errs := make([]error, workers)
	var wg sync.WaitGroup
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			devices[i], errs[i] = Attach(backing)
		}(i)
	}
	wg.Wait()

	seen := map[string]bool{}
	for i := range devices {
		if errs[i] != nil {
			t.Errorf("worker %d: %v", i, errs[i])
			continue
		}
		if seen[devices[i]] {
			t.Errorf("%s handed to two workers", devices[i])
		}
		seen[devices[i]] = true
	}
}
