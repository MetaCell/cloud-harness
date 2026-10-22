package mount

// Scenario tests for the volume lifecycle as the provisioner, the watchdog and
// a pod restart drive it, including each sequence that left osb2 unable to
// provision any volume (Sep–Oct 2026). Root-only steps are faked: see fakeSystem.

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"sync"
	"testing"
)

const testSize = 1 << 20

// fakeSystem stands in for the root-only steps (mkfs, the loop mount, loop
// cleanup and exportfs) and points the exports config dir and etab at temp
// paths. Its exportfs mirrors nfs-utils: a fragment naming a missing path or a
// non-directory is only warned about and still lands in etab, but the run
// exits 1. Fake mounts are not visible to IsMounted.
type fakeSystem struct {
	exports string // stands in for /exports

	mu        sync.Mutex
	images    int      // filesystems formatted so far
	mounts    []string // mountpoints mounted so far
	mkfsErr   error    // fail the next mkfs
	mountErr  error    // fail the next mount
	exportErr error    // fail the next exportfs before it writes etab
}

func newFakeSystem(t *testing.T) *fakeSystem {
	t.Helper()
	f := &fakeSystem{exports: t.TempDir()}

	oldFormat, oldMount, oldClean, oldExportfs := formatExt4, mountQuota, cleanLoops, runExportfs
	oldConfigDir, oldEtab := exportsConfigDir, etabPath
	t.Cleanup(func() {
		formatExt4, mountQuota, cleanLoops, runExportfs = oldFormat, oldMount, oldClean, oldExportfs
		exportsConfigDir, etabPath = oldConfigDir, oldEtab
	})

	exportsConfigDir = t.TempDir()
	etabPath = filepath.Join(t.TempDir(), "etab")
	formatExt4 = f.mkfs
	mountQuota = f.mount
	cleanLoops = func([]string) {}
	runExportfs = f.exportfs
	return f
}

func (f *fakeSystem) mkfs(quotaFile string) ([]byte, error) {
	f.mu.Lock()
	defer f.mu.Unlock()
	if err := f.mkfsErr; err != nil {
		f.mkfsErr = nil
		return []byte("mkfs failed"), err
	}
	f.images++
	return nil, os.WriteFile(quotaFile, []byte(fmt.Sprintf("image-%d", f.images)), 0644)
}

func (f *fakeSystem) mount(quotaFile, mountpoint string) error {
	f.mu.Lock()
	defer f.mu.Unlock()
	if err := f.mountErr; err != nil {
		f.mountErr = nil
		return err
	}
	if _, err := os.Stat(quotaFile); err != nil {
		return err
	}
	f.mounts = append(f.mounts, mountpoint)
	return nil
}

func (f *fakeSystem) mountCount() int {
	f.mu.Lock()
	defer f.mu.Unlock()
	return len(f.mounts)
}

func (f *fakeSystem) exportfs() ([]byte, error) {
	f.mu.Lock()
	err := f.exportErr
	f.exportErr = nil
	f.mu.Unlock()
	if err != nil {
		return []byte("exportfs failed"), err
	}

	fragments, err := filepath.Glob(filepath.Join(exportsConfigDir, "*.exports"))
	if err != nil {
		return nil, err
	}
	var etab, out strings.Builder
	for _, fragment := range fragments {
		data, err := os.ReadFile(fragment)
		if err != nil {
			return nil, err
		}
		fields := strings.Fields(string(data))
		path := fields[0]
		if fi, err := os.Stat(path); err != nil {
			fmt.Fprintf(&out, "exportfs: Failed to stat %s: %v\n", path, err)
		} else if !fi.IsDir() {
			fmt.Fprintf(&out, "exportfs: %s is not a directory. Remote access will fail\n", path)
		}
		fmt.Fprintf(&etab, "%s\t%s\n", path, fields[1])
	}
	if err := os.WriteFile(etabPath, []byte(etab.String()), 0644); err != nil {
		return nil, err
	}
	if out.Len() > 0 {
		return []byte(out.String()), errors.New("exit status 1")
	}
	return nil, nil
}

// volume returns the path the provisioner gives a claim's volume.
func (f *fakeSystem) volume(claim string) string {
	return filepath.Join(f.exports, "osb2-"+claim+"-pvc-0000")
}

// stuckByOldRelease reproduces a claim the previous release could never
// provision: its retry renamed the earlier quota file onto the mountpoint and
// made a fresh one, and mount-all then wrote an export for the non-directory.
func (f *fakeSystem) stuckByOldRelease(t *testing.T, claim string) string {
	t.Helper()
	mp := f.volume(claim)
	writeFile(t, mp, "image-old")
	writeFile(t, mp+".quota", "image-fresh")
	if err := WriteExport(mp); err != nil {
		t.Fatal(err)
	}
	return mp
}

func readFile(t *testing.T, path string) string {
	t.Helper()
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	return string(data)
}

func mustCreate(t *testing.T, mp string) {
	t.Helper()
	if err := Create(mp, testSize); err != nil {
		t.Fatalf("Create(%s): %v", mp, err)
	}
}

func assertProvisioned(t *testing.T, mp string) {
	t.Helper()
	if !isDir(mp) {
		t.Errorf("%s is not a directory", mp)
	}
	if !exists(mp + ".quota") {
		t.Errorf("%s.quota is missing", mp)
	}
	if !exists(pvExportFile(filepath.Base(mp))) {
		t.Errorf("no export fragment for %s", mp)
	}
	if !isExported(mp) {
		t.Errorf("%s is not in etab", mp)
	}
}

func assertNothingLeft(t *testing.T, mp string) {
	t.Helper()
	for _, p := range []string{mp, mp + ".quota", pvExportFile(filepath.Base(mp))} {
		if exists(p) {
			t.Errorf("%s left behind", p)
		}
	}
}

// assertDeleted checks the state Delete hands to the provisioner to archive or
// remove: the volume image as a regular file at the mountpoint, nothing else.
func assertDeleted(t *testing.T, mp, image string) {
	t.Helper()
	if got := readFile(t, mp); got != image {
		t.Errorf("%s holds %q, want the volume image %q", mp, got, image)
	}
	if exists(mp + ".quota") {
		t.Errorf("%s.quota left behind", mp)
	}
	if exists(pvExportFile(filepath.Base(mp))) {
		t.Errorf("export fragment for %s left behind", mp)
	}
}

func TestCreate(t *testing.T) {
	f := newFakeSystem(t)
	mp := f.volume("workspace-1")
	mustCreate(t, mp)
	assertProvisioned(t, mp)
}

// One bad fragment makes every `exportfs -r` exit 1. Create used to report that
// as its own failure even though it had exported the new volume.
func TestCreateWhileAnotherExportIsBroken(t *testing.T) {
	f := newFakeSystem(t)
	f.stuckByOldRelease(t, "workspace-1")
	if err := ReloadExports(); err == nil {
		t.Fatal("exportfs succeeded with a non-directory export; the fake no longer mirrors nfs-utils")
	}

	mp := f.volume("workspace-2")
	mustCreate(t, mp)
	assertProvisioned(t, mp)
}

// The provisioner retries a failed Create on the same path. The old Create
// "cleaned up" with Delete, which renamed the quota file onto the mountpoint,
// so every retry failed with "not a directory". And a claim deleted while
// still Pending gets no Delete at all, so a failed Create must leave nothing.
func TestFailedCreateLeavesNothingAndRetrySucceeds(t *testing.T) {
	boom := errors.New("boom")
	for name, inject := range map[string]func(*fakeSystem){
		"mkfs fails":     func(f *fakeSystem) { f.mkfsErr = boom },
		"mount fails":    func(f *fakeSystem) { f.mountErr = boom },
		"exportfs fails": func(f *fakeSystem) { f.exportErr = boom },
	} {
		t.Run(name, func(t *testing.T) {
			f := newFakeSystem(t)
			mp := f.volume("workspace-1")
			inject(f)
			if err := Create(mp, testSize); err == nil {
				t.Fatal("Create succeeded despite the injected failure")
			}
			assertNothingLeft(t, mp)

			mustCreate(t, mp)
			assertProvisioned(t, mp)
		})
	}
}

// `nfsvol create` killed part-way, e.g. by a spot-node preemption: the
// provisioner's retry must start over from whatever was left.
func TestCreateRecoversFromInterruptedCreate(t *testing.T) {
	for name, leave := range map[string]func(t *testing.T, mp string){
		"during mkfs": func(t *testing.T, mp string) {
			writeFile(t, mp+".quota", "")
		},
		"before mount": func(t *testing.T, mp string) {
			writeFile(t, mp+".quota", "image-0")
			if err := os.Mkdir(mp, 0777); err != nil {
				t.Fatal(err)
			}
		},
		"before exports reload": func(t *testing.T, mp string) {
			writeFile(t, mp+".quota", "image-0")
			if err := os.Mkdir(mp, 0777); err != nil {
				t.Fatal(err)
			}
			if err := WriteExport(mp); err != nil {
				t.Fatal(err)
			}
		},
	} {
		t.Run(name, func(t *testing.T) {
			f := newFakeSystem(t)
			mp := f.volume("workspace-1")
			leave(t, mp)
			mustCreate(t, mp)
			assertProvisioned(t, mp)
		})
	}
}

// After upgrading, the provisioner's next retry heals a claim the previous
// release left stuck, and the bad export stops failing everyone else.
func TestCreateHealsClaimStuckByOldRelease(t *testing.T) {
	f := newFakeSystem(t)
	mp := f.stuckByOldRelease(t, "workspace-1")

	mustCreate(t, mp)
	assertProvisioned(t, mp)
	aside, _ := filepath.Glob(mp + ".discarded-*")
	if len(aside) != 1 || readFile(t, aside[0]) != "image-old" {
		t.Errorf("old image not moved aside intact: %v", aside)
	}
	if err := ReloadExports(); err != nil {
		t.Errorf("exportfs still failing once the stuck claim healed: %v", err)
	}
}

// kubectl delete pvc: the provisioner runs `nfsvol delete`, then archives or
// removes the regular file Delete leaves at the mountpoint. Nothing may bring
// the volume back: not the watchdog, not a pod restart.
func TestDeletePVC(t *testing.T) {
	f := newFakeSystem(t)
	mp := f.volume("workspace-1")
	mustCreate(t, mp)
	image := readFile(t, mp+".quota")

	if err := Delete(mp); err != nil {
		t.Fatalf("Delete: %v", err)
	}
	assertDeleted(t, mp, image)
	if isExported(mp) {
		t.Errorf("%s still in etab", mp)
	}

	mounts := f.mountCount()
	if err := RemountIfStale(mp); err != nil {
		t.Errorf("RemountIfStale: %v", err)
	}
	if err := MountAll(f.exports); err != nil {
		t.Errorf("MountAll: %v", err)
	}
	assertDeleted(t, mp, image)
	if f.mountCount() != mounts {
		t.Errorf("deleted volume was mounted again: %v", f.mounts[mounts:])
	}
}

// The provisioner retries Delete until archiving succeeds, so Delete can run
// again after it already renamed the image into place (pod killed before the
// archive rename). The old Delete removed the image on that second run.
func TestDeletePVCRetriedBeforeArchive(t *testing.T) {
	f := newFakeSystem(t)
	mp := f.volume("workspace-1")
	mustCreate(t, mp)
	image := readFile(t, mp+".quota")

	for i := 0; i < 2; i++ {
		if err := Delete(mp); err != nil {
			t.Fatalf("Delete #%d: %v", i+1, err)
		}
	}
	assertDeleted(t, mp, image)
}

// Delete interrupted after removing the mountpoint but before renaming the
// quota file. The watchdog and mount-all used to recreate the mountpoint and
// remount it, resurrecting a volume whose PV was going away.
func TestDeletePVCInterruptedBeforeRename(t *testing.T) {
	f := newFakeSystem(t)
	mp := f.volume("workspace-1")
	mustCreate(t, mp)
	image := readFile(t, mp+".quota")
	if err := os.Remove(mp); err != nil { // as far as Delete got
		t.Fatal(err)
	}
	mounts := f.mountCount()

	if err := RemountIfStale(mp); err != nil {
		t.Errorf("RemountIfStale: %v", err)
	}
	if err := MountAll(f.exports); err == nil {
		t.Error("MountAll reported success for a half-deleted volume")
	}
	if exists(mp) || f.mountCount() != mounts {
		t.Fatalf("half-deleted volume was brought back (mountpoint exists: %v, mounts: %v)", exists(mp), f.mounts[mounts:])
	}
	if err := ReloadExports(); err != nil { // run_nfs.sh does this after mount-all
		t.Errorf("exportfs -r: %v", err)
	}
	if isExported(mp) {
		t.Errorf("half-deleted %s is still exported", mp)
	}

	// The provisioner's retry finishes the job.
	if err := Delete(mp); err != nil {
		t.Fatalf("Delete: %v", err)
	}
	assertDeleted(t, mp, image)
}

func TestDeletePVCWhileAnotherExportIsBroken(t *testing.T) {
	f := newFakeSystem(t)
	mp := f.volume("workspace-1")
	mustCreate(t, mp)
	image := readFile(t, mp+".quota")
	f.stuckByOldRelease(t, "workspace-2")

	if err := Delete(mp); err != nil {
		t.Fatalf("Delete: %v", err)
	}
	assertDeleted(t, mp, image)
}

// A pod restart with every kind of leftover seen on osb2. mount-all used to
// write an export for each, and one non-directory among them failed every
// Create from then on.
func TestPodRestartWithLeftovers(t *testing.T) {
	f := newFakeSystem(t)
	healthy := f.volume("workspace-1")
	mustCreate(t, healthy)

	deleted := f.volume("workspace-2")
	mustCreate(t, deleted)
	if err := Delete(deleted); err != nil {
		t.Fatal(err)
	}

	interrupted := f.volume("workspace-3")
	mustCreate(t, interrupted)
	if err := os.Remove(interrupted); err != nil {
		t.Fatal(err)
	}

	stuck := f.stuckByOldRelease(t, "workspace-4")
	writeFile(t, filepath.Join(f.exports, "archived-osb2-workspace-5-pvc-0000"), "image-archived")

	_ = MountAll(f.exports) // reports the leftovers it cannot mount
	if err := ReloadExports(); err != nil {
		t.Fatalf("exportfs -r after restart: %v", err)
	}
	got, _ := filepath.Glob(filepath.Join(exportsConfigDir, "*.exports"))
	if want := []string{pvExportFile(filepath.Base(healthy))}; !reflect.DeepEqual(got, want) {
		t.Errorf("fragments = %v, want %v", got, want)
	}
	if !isExported(healthy) {
		t.Errorf("%s not exported after restart", healthy)
	}
	for _, mp := range []string{interrupted, stuck} {
		if isDir(mp) {
			t.Errorf("mount-all turned leftover %s into a mountpoint", mp)
		}
	}
}

// A stale mount is remounted even while some other volume's export is broken;
// the remount used to be reported as failed.
func TestWatchdogRemountsWhileAnotherExportIsBroken(t *testing.T) {
	f := newFakeSystem(t)
	mp := f.volume("workspace-1")
	mustCreate(t, mp) // fake mounts are invisible to IsMounted, so mp looks stale
	f.stuckByOldRelease(t, "workspace-2")
	mounts := f.mountCount()

	if err := RemountIfStale(mp); err != nil {
		t.Fatalf("RemountIfStale: %v", err)
	}
	if f.mountCount() != mounts+1 {
		t.Error("stale volume was not remounted")
	}
}
