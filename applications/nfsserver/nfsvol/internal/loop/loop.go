package loop

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"

	"golang.org/x/sys/unix"
)

const loopControlPath = "/dev/loop-control"

// attachRetries bounds how many times Attach asks for a new free device after
// losing one to a concurrent attacher.
const attachRetries = 10

// attachMu serialises GetFree → LOOP_SET_FD within this process, so the
// concurrent mount-all and watchdog workers do not all race for the same free
// device. It cannot serialise other processes (e.g. an `nfsvol create` run by
// the provisioner); the retry in Attach covers those.
var attachMu sync.Mutex

// GetFree returns the index of a loop device that is currently unbound,
// allocating a new one if none is. The kernel does NOT reserve it: concurrent
// callers get the same index until one of them binds it, after which
// LOOP_SET_FD fails with EBUSY for the others (see Attach).
func GetFree() (int, error) {
	ctrl, err := os.OpenFile(loopControlPath, os.O_RDWR, 0)
	if err != nil {
		return 0, fmt.Errorf("open %s: %w", loopControlPath, err)
	}
	defer ctrl.Close()
	n, err := unix.IoctlRetInt(int(ctrl.Fd()), unix.LOOP_CTL_GET_FREE)
	if err != nil {
		return 0, fmt.Errorf("LOOP_CTL_GET_FREE: %w", err)
	}
	return n, nil
}

// DevPath returns the device path for loop index n.
func DevPath(n int) string {
	return fmt.Sprintf("/dev/loop%d", n)
}

// EnsureDevice creates the block device node for /dev/loopN if it does not exist.
func EnsureDevice(n int) error {
	path := DevPath(n)
	if _, err := os.Stat(path); err == nil {
		return nil
	}
	dev := unix.Mkdev(7, uint32(n))
	return unix.Mknod(path, unix.S_IFBLK|0666, int(dev))
}

// Attach attaches backingFile to a free loop device and returns the loop device path.
func Attach(backingFile string) (string, error) {
	bf, err := os.OpenFile(backingFile, os.O_RDWR, 0)
	if err != nil {
		return "", fmt.Errorf("open backing file %s: %w", backingFile, err)
	}
	defer bf.Close()

	attachMu.Lock()
	defer attachMu.Unlock()

	for attempt := 0; ; attempt++ {
		loopPath, err := attachFree(bf)
		if err == nil {
			return loopPath, nil
		}
		// EBUSY: another attacher bound the device between GetFree and
		// LOOP_SET_FD. ENXIO: the device went away in that same window.
		// Either way, ask the kernel for a new free device.
		if attempt < attachRetries && (errors.Is(err, unix.EBUSY) || errors.Is(err, unix.ENXIO)) {
			continue
		}
		return "", err
	}
}

// attachFree binds bf to a free loop device; a variable so tests can replace it.
var attachFree = attachFreeDevice

// attachFreeDevice binds bf to the loop device GetFree currently reports as free.
func attachFreeDevice(bf *os.File) (string, error) {
	n, err := GetFree()
	if err != nil {
		return "", err
	}
	if err := EnsureDevice(n); err != nil {
		return "", fmt.Errorf("ensure device loop%d: %w", n, err)
	}
	loopPath := DevPath(n)

	lf, err := os.OpenFile(loopPath, os.O_RDWR, 0)
	if err != nil {
		return "", fmt.Errorf("open loop device %s: %w", loopPath, err)
	}
	defer lf.Close()

	if err := unix.IoctlSetInt(int(lf.Fd()), unix.LOOP_SET_FD, int(bf.Fd())); err != nil {
		return "", fmt.Errorf("LOOP_SET_FD on %s: %w", loopPath, err)
	}
	return loopPath, nil
}

// Detach disassociates the backing file from loopPath.
func Detach(loopPath string) error {
	lf, err := os.OpenFile(loopPath, os.O_RDONLY, 0)
	if err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		return fmt.Errorf("open %s: %w", loopPath, err)
	}
	defer lf.Close()
	if err := unix.IoctlSetInt(int(lf.Fd()), unix.LOOP_CLR_FD, 0); err != nil {
		return fmt.Errorf("LOOP_CLR_FD on %s: %w", loopPath, err)
	}
	return nil
}

// FindByBacking returns the first loop device path backed by the given file,
// or "" if none is found.
func FindByBacking(backingFile string) (string, error) {
	abs, err := filepath.Abs(backingFile)
	if err != nil {
		abs = backingFile
	}
	entries, err := filepath.Glob("/sys/block/loop*/loop/backing_file")
	if err != nil {
		return "", err
	}
	for _, entry := range entries {
		data, err := os.ReadFile(entry)
		if err != nil {
			continue
		}
		backing := strings.TrimSpace(string(data))
		backing = strings.TrimSuffix(backing, " (deleted)")
		if backing == abs {
			parts := strings.Split(entry, "/")
			return "/dev/" + parts[3], nil
		}
	}
	return "", nil
}

// DetachByBacking finds and detaches ALL loop devices backing the given file.
// The NFS server pod shares the host mount namespace; if the previous pod was
// killed without graceful shutdown the loop device may still be mounted in the
// host namespace, causing LOOP_CLR_FD to fail with EBUSY. A lazy unmount of
// the associated mountpoint (backing path without ".quota" suffix) is attempted
// first so LOOP_CLR_FD can succeed.
// It is a no-op if no loop device is associated with the file.
func DetachByBacking(backingFile string) error {
	abs, err := filepath.Abs(backingFile)
	if err != nil {
		abs = backingFile
	}
	entries, _ := filepath.Glob("/sys/block/loop*/loop/backing_file")
	for _, entry := range entries {
		data, err := os.ReadFile(entry)
		if err != nil {
			continue
		}
		backing := strings.TrimSpace(string(data))
		backing = strings.TrimSuffix(backing, " (deleted)")
		if backing == abs {
			// Lazy-unmount the mountpoint so the loop device is no longer
			// "in use" before calling LOOP_CLR_FD.
			mountpoint := strings.TrimSuffix(abs, ".quota")
			_ = unix.Unmount(mountpoint, unix.MNT_DETACH)
			parts := strings.Split(entry, "/")
			_ = Detach("/dev/" + parts[3])
		}
	}
	return nil
}

// CleanStale detaches all loop devices whose kernel-reported backing file is marked deleted.
func CleanStale() {
	entries, _ := filepath.Glob("/sys/block/loop*/loop/backing_file")
	for _, entry := range entries {
		data, err := os.ReadFile(entry)
		if err != nil {
			continue
		}
		if strings.Contains(string(data), "(deleted)") {
			parts := strings.Split(entry, "/")
			_ = Detach("/dev/" + parts[3])
		}
	}
}

// CleanByFiles detaches ALL loop devices whose backing file is in the given set.
// It builds the loop->backing index exactly once (O(total_loop_devices)), making
// it efficient for bulk cleanup at startup regardless of how many files are passed.
// A lazy unmount of each associated mountpoint is attempted before LOOP_CLR_FD so
// that zombie mounts left by a killed previous pod do not block the detach.
func CleanByFiles(backingFiles []string) {
	want := make(map[string]bool, len(backingFiles))
	for _, f := range backingFiles {
		abs, err := filepath.Abs(f)
		if err != nil {
			abs = f
		}
		want[abs] = true
	}

	entries, _ := filepath.Glob("/sys/block/loop*/loop/backing_file")
	for _, entry := range entries {
		data, err := os.ReadFile(entry)
		if err != nil {
			continue
		}
		backing := strings.TrimSpace(string(data))
		backing = strings.TrimSuffix(backing, " (deleted)")
		if want[backing] {
			// Lazy-unmount the mountpoint before detaching. The NFS server pod
			// shares the host mount namespace; zombie mounts from the previous
			// pod keep the loop device in-use and cause LOOP_CLR_FD to fail.
			mountpoint := strings.TrimSuffix(backing, ".quota")
			_ = unix.Unmount(mountpoint, unix.MNT_DETACH)
			parts := strings.Split(entry, "/")
			_ = Detach("/dev/" + parts[3])
		}
	}
}
