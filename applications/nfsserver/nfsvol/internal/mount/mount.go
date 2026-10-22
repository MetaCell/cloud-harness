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
	"time"

	"golang.org/x/sys/unix"

	"metacell/nfsvol/internal/loop"
)

// maxUnmounts bounds how many stacked mounts unmountAll peels off a
// mountpoint before giving up.
const maxUnmounts = 8

// Indirections over the steps that need root, so tests can replace them.
var (
	formatExt4 = func(quotaFile string) ([]byte, error) {
		return exec.Command("mkfs.ext4", "-F", quotaFile).CombinedOutput()
	}
	mountQuota = mountQuotaFile
	cleanLoops = func(quotaFiles []string) {
		loop.CleanStale()
		loop.CleanByFiles(quotaFiles)
	}
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

// isDir reports whether path exists and is a directory.
func isDir(path string) bool {
	fi, err := os.Stat(path)
	return err == nil && fi.IsDir()
}

// mountOne mounts the quota file for mountpoint. Idempotent: skips if already mounted.
// The mountpoint directory must already exist: only Create makes it, after
// mkfs, so a missing one means the volume is mid-Create or mid-Delete, and
// mounting it would mount a half-written filesystem or resurrect a deleted
// volume.
func mountOne(mountpoint string) error {
	if IsMounted(mountpoint) {
		return nil
	}
	if !isDir(mountpoint) {
		return fmt.Errorf("%s is not a directory: volume is being created or deleted", mountpoint)
	}
	if err := mountQuota(mountpoint+".quota", mountpoint); err != nil {
		return err
	}
	return os.Chmod(mountpoint, 0777)
}

// mountQuotaFile attaches quotaFile to a loop device and mounts it on mountpoint.
func mountQuotaFile(quotaFile, mountpoint string) error {
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
	return nil
}

// unmountAll lazily unmounts mountpoint until nothing is mounted there: a
// watchdog remount racing Create can stack mounts.
func unmountAll(mountpoint string) error {
	for i := 0; IsMounted(mountpoint); i++ {
		if i == maxUnmounts {
			return fmt.Errorf("%s still mounted after %d unmounts", mountpoint, maxUnmounts)
		}
		if err := unix.Unmount(mountpoint, unix.MNT_DETACH); err != nil {
			return fmt.Errorf("unmount %s: %w", mountpoint, err)
		}
	}
	return nil
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
		// Still regenerate /etc/exports.d/ so any stale fragments from a
		// previous incarnation are cleaned up.
		if err := RegenerateExportsFromQuotas(exportsDir); err != nil {
			log.Printf("mount-all: regenerate exports: %v", err)
		}
		return nil
	}

	// Detach ALL loop devices pointing to quota files in a single O(loop_count)
	// pass. This clears stale devices accumulated from prior crash-loop restarts
	// without the O(loop_count × quota_count) cost of per-file DetachByBacking.
	log.Printf("mount-all: cleaning stale loop devices for %d quota files", len(quotaFiles))
	cleanLoops(quotaFiles)

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
	// Regenerate exports.d deterministically from the quota files we just
	// processed. This provides stable fsids even after a node reschedule.
	// run_nfs.sh will call `exportfs -r` a few lines later, so no explicit
	// reload needed here.
	if err := RegenerateExportsFromQuotas(exportsDir); err != nil {
		log.Printf("mount-all: regenerate exports: %v", err)
	}

	if failed > 0 {
		return fmt.Errorf("%d of %d mounts failed", failed, len(quotaFiles))
	}
	return nil
}

// Create makes a new quota-backed directory: creates the sparse backing file,
// formats it ext4, mounts it, and sets permissions.
func Create(mountpoint string, sizeBytes int64) (err error) {
	quotaFile := mountpoint + ".quota"

	// Clean up any pre-existing state left from a failed previous attempt.
	if err := discardPartial(mountpoint); err != nil {
		return err
	}
	// Roll back on failure: the provisioner retries, but a claim deleted while
	// still Pending gets no Delete, so anything left here would be orphaned.
	defer func() {
		if err != nil {
			if cerr := discardPartial(mountpoint); cerr != nil {
				log.Printf("create: roll back %s: %v", mountpoint, cerr)
			}
		}
	}()

	if err := createQuotaFile(quotaFile, sizeBytes); err != nil {
		return err
	}

	if out, err := formatExt4(quotaFile); err != nil {
		return fmt.Errorf("mkfs.ext4: %w\n%s", err, out)
	}

	// Make the mountpoint only now: the watchdog and mount-all leave a volume
	// alone until it exists, so they never mount a half-written filesystem.
	if err := os.Mkdir(mountpoint, 0777); err != nil {
		return fmt.Errorf("mkdir %s: %w", mountpoint, err)
	}
	if err := mountOne(mountpoint); err != nil {
		return err
	}
	if err := WriteExport(mountpoint); err != nil {
		return fmt.Errorf("write export for %s: %w", mountpoint, err)
	}
	return reloadExportsFor(mountpoint)
}

// discardPartial removes what a previous, failed Create left at mountpoint so
// Create can start from scratch. It must not use Delete: Delete renames the
// quota file onto the mountpoint path, leaving a regular file there that makes
// every later attempt fail in mountOne with "not a directory".
//
// The provisioner names the path after the PV (pvc-<claim uid>) unless the
// StorageClass sets pathPattern, so whatever is found here belongs to this
// never-provisioned claim and holds no user data. Because pathPattern can make
// paths reusable, it still refuses to touch a mounted volume that is not empty
// and moves a regular file at the mountpoint aside instead of deleting it. The
// one thing it removes unchecked is an unmounted leftover quota file.
func discardPartial(mountpoint string) error {
	quotaFile := mountpoint + ".quota"

	if IsMounted(mountpoint) {
		entries, err := os.ReadDir(mountpoint)
		if err != nil {
			return fmt.Errorf("read %s: %w", mountpoint, err)
		}
		for _, e := range entries {
			if e.Name() != "lost+found" {
				return fmt.Errorf("refusing to recreate %s: it is mounted and not empty", mountpoint)
			}
		}
	}
	if err := unmountAll(mountpoint); err != nil {
		return err
	}
	_ = loop.DetachByBacking(quotaFile)

	if err := RemoveExport(mountpoint); err != nil {
		return fmt.Errorf("remove export for %s: %w", mountpoint, err)
	}

	if fi, err := os.Lstat(mountpoint); err == nil {
		if fi.IsDir() {
			// Not RemoveAll: once unmounted this must be an empty mountpoint.
			if err := os.Remove(mountpoint); err != nil {
				return fmt.Errorf("remove %s: %w", mountpoint, err)
			}
		} else {
			aside := fmt.Sprintf("%s.discarded-%d", mountpoint, time.Now().Unix())
			log.Printf("create: moving leftover %s aside to %s", mountpoint, aside)
			if err := os.Rename(mountpoint, aside); err != nil {
				return fmt.Errorf("move %s aside: %w", mountpoint, err)
			}
		}
	}

	if err := os.Remove(quotaFile); err != nil && !os.IsNotExist(err) {
		return fmt.Errorf("remove %s: %w", quotaFile, err)
	}
	return nil
}

// Delete unmounts the loop-backed directory and renames the quota file to the
// mountpoint path (matching rmlimdir.sh behavior: caller decides final disposition).
func Delete(mountpoint string) error {
	quotaFile := mountpoint + ".quota"

	// Lazy unmount: detaches from the filesystem namespace immediately while
	// still letting active users finish. Stop if anything stays mounted:
	// removing the mountpoint below would then delete the volume's data.
	if err := unmountAll(mountpoint); err != nil {
		return err
	}

	_ = loop.DetachByBacking(quotaFile)
	// A regular file here is the image an earlier, interrupted Delete already
	// renamed into place; the provisioner retries until it is archived, so
	// only remove the (empty) mountpoint directory.
	if isDir(mountpoint) {
		_ = os.RemoveAll(mountpoint)
	}

	// Rename quota file to the mountpoint path so the raw ext4 data is preserved
	// as a regular file. The provisioner may then archive or remove it.
	if _, err := os.Stat(quotaFile); err == nil {
		if err := os.Rename(quotaFile, mountpoint); err != nil {
			log.Printf("delete: rename %s → %s: %v", quotaFile, mountpoint, err)
		}
	}

	if err := RemoveExport(mountpoint); err != nil {
		log.Printf("delete: remove export for %s: %v", mountpoint, err)
	}
	if err := ReloadExports(); err != nil {
		log.Printf("delete: exportfs -r: %v", err)
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
	// No mountpoint directory: the volume is mid-Create (the directory only
	// appears after mkfs) or mid-Delete, or a leftover of a failed Create.
	// None is the watchdog's to repair, and mounting a quota file that mkfs
	// is still writing races with Create.
	if fi, err := os.Lstat(mountpoint); os.IsNotExist(err) || (err == nil && !fi.IsDir()) {
		return nil
	}
	if IsMounted(mountpoint) {
		return nil
	}
	log.Printf("watchdog: stale mount at %s, remounting", mountpoint)
	if err := mountOne(mountpoint); err != nil {
		return err
	}
	// Re-assert the exports fragment — the fsid is deterministic from the
	// PV name, so clients will keep using the same file handles; but we
	// refresh the fragment in case /etc/exports.d/ lost it somehow.
	if err := WriteExport(mountpoint); err != nil {
		log.Printf("watchdog: write export for %s: %v", mountpoint, err)
	}
	return reloadExportsFor(mountpoint)
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
