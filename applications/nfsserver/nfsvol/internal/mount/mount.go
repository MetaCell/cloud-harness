package mount

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"sync"

	"golang.org/x/sys/unix"

	"metacell/nfsvol/internal/loop"
)

// IsMounted reports whether path is a mountpoint by comparing its device ID to
// its parent's. Returns false if path does not exist.
func IsMounted(path string) bool {
	var st, stParent unix.Stat_t
	if err := unix.Stat(path, &st); err != nil {
		return false
	}
	if err := unix.Stat(filepath.Dir(path), &stParent); err != nil {
		return false
	}
	return st.Dev != stParent.Dev
}

// mountOne mounts the quota file for mountpoint. Idempotent: skips if already mounted.
func mountOne(mountpoint string) error {
	quotaFile := mountpoint + ".quota"

	if IsMounted(mountpoint) {
		return nil
	}

	if err := os.MkdirAll(mountpoint, 0777); err != nil {
		return fmt.Errorf("mkdir %s: %w", mountpoint, err)
	}

	// Detach any stale loop device still associated with this backing file.
	_ = loop.DetachByBacking(quotaFile)

	loopPath, err := loop.Attach(quotaFile)
	if err != nil {
		return fmt.Errorf("attach %s: %w", quotaFile, err)
	}

	if err := unix.Mount(loopPath, mountpoint, "ext4", 0, ""); err != nil {
		_ = loop.Detach(loopPath)
		return fmt.Errorf("mount %s → %s: %w", loopPath, mountpoint, err)
	}

	return os.Chmod(mountpoint, 0777)
}

// MountAll mounts all *.quota files under exportsDir concurrently.
// It first cleans stale loop devices, then enumerates backing files and mounts
// each in a bounded worker pool. Logs individual failures but returns an aggregate
// error only if any mounts fail.
func MountAll(exportsDir string) error {
	loop.CleanStale()

	quotaFiles, err := filepath.Glob(filepath.Join(exportsDir, "*.quota"))
	if err != nil {
		return err
	}
	if len(quotaFiles) == 0 {
		log.Println("mount-all: no quota files found")
		return nil
	}
	log.Printf("mount-all: mounting %d volumes", len(quotaFiles))

	workers := runtime.NumCPU() * 2
	if workers > 32 {
		workers = 32
	}
	if workers < 1 {
		workers = 1
	}

	type result struct {
		path string
		err  error
	}

	jobs := make(chan string, len(quotaFiles))
	results := make(chan result, len(quotaFiles))

	var wg sync.WaitGroup
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for qf := range jobs {
				mp := strings.TrimSuffix(qf, ".quota")
				err := mountOne(mp)
				results <- result{mp, err}
			}
		}()
	}

	for _, qf := range quotaFiles {
		jobs <- qf
	}
	close(jobs)

	wg.Wait()
	close(results)

	var failed int
	for r := range results {
		if r.err != nil {
			log.Printf("mount-all: FAILED %s: %v", r.path, r.err)
			failed++
		} else {
			log.Printf("mount-all: OK %s", r.path)
		}
	}
	if failed > 0 {
		return fmt.Errorf("%d of %d mounts failed", failed, len(quotaFiles))
	}
	return nil
}

// Create makes a new quota-backed directory: creates the sparse backing file,
// formats it ext4, mounts it, and sets permissions.
func Create(mountpoint string, sizeBytes int64) error {
	quotaFile := mountpoint + ".quota"

	// Clean up any pre-existing state left from a failed previous attempt.
	_ = Delete(mountpoint)

	if err := createQuotaFile(quotaFile, sizeBytes); err != nil {
		return err
	}

	cmd := exec.Command("mkfs.ext4", "-F", quotaFile)
	if out, err := cmd.CombinedOutput(); err != nil {
		_ = os.Remove(quotaFile)
		return fmt.Errorf("mkfs.ext4: %w\n%s", err, out)
	}

	return mountOne(mountpoint)
}

// Delete unmounts the loop-backed directory and renames the quota file to the
// mountpoint path (matching rmlimdir.sh behavior: caller decides final disposition).
func Delete(mountpoint string) error {
	quotaFile := mountpoint + ".quota"

	if IsMounted(mountpoint) {
		// MNT_DETACH = lazy unmount: detaches from the filesystem namespace
		// immediately while still letting active users finish.
		if err := unix.Unmount(mountpoint, unix.MNT_DETACH); err != nil {
			log.Printf("delete: unmount %s: %v (continuing)", mountpoint, err)
		}
	}

	_ = loop.DetachByBacking(quotaFile)
	_ = os.RemoveAll(mountpoint)

	// Rename quota file to the mountpoint path so the raw ext4 data is preserved
	// as a regular file. The provisioner may then archive or remove it.
	if _, err := os.Stat(quotaFile); err == nil {
		if err := os.Rename(quotaFile, mountpoint); err != nil {
			log.Printf("delete: rename %s → %s: %v", quotaFile, mountpoint, err)
		}
	}
	return nil
}

// RemountIfStale checks a single mountpoint and remounts it if stale.
// It skips paths whose backing quota file no longer exists.
func RemountIfStale(mountpoint string) error {
	quotaFile := mountpoint + ".quota"
	if _, err := os.Stat(quotaFile); err != nil {
		return nil // quota file gone, nothing to do
	}
	if IsMounted(mountpoint) {
		return nil
	}
	log.Printf("watchdog: stale mount at %s, remounting", mountpoint)
	return mountOne(mountpoint)
}

func createQuotaFile(path string, size int64) error {
	f, err := os.Create(path)
	if err != nil {
		return fmt.Errorf("create %s: %w", path, err)
	}
	defer f.Close()
	if err := f.Truncate(size); err != nil {
		return fmt.Errorf("truncate %s to %d: %w", path, size, err)
	}
	return nil
}
