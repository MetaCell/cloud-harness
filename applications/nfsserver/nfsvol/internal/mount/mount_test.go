package mount

import (
	"os"
	"path/filepath"
	"testing"
)

func exists(path string) bool {
	_, err := os.Lstat(path)
	return err == nil
}

// The state the old Delete-based cleanup left after a failed Create: the
// previous quota file renamed onto the mountpoint, plus a fresh quota file.
func TestDiscardPartialMovesFileAtMountpointAside(t *testing.T) {
	useTempExportsConfig(t)
	mp := filepath.Join(t.TempDir(), "osb2-workspace-1-pvc-a")
	writeFile(t, mp, "old image")
	writeFile(t, mp+".quota", "fresh image")
	fragment := pvExportFile(filepath.Base(mp))
	writeFile(t, fragment, mp+" *(rw)\n")

	if err := discardPartial(mp); err != nil {
		t.Fatalf("discardPartial: %v", err)
	}
	for _, p := range []string{mp, mp + ".quota", fragment} {
		if exists(p) {
			t.Errorf("%s still exists", p)
		}
	}
	aside, _ := filepath.Glob(mp + ".discarded-*")
	if len(aside) != 1 {
		t.Fatalf("discarded files = %v, want exactly one", aside)
	}
	if data, _ := os.ReadFile(aside[0]); string(data) != "old image" {
		t.Errorf("discarded file holds %q, want the old image", data)
	}
}

func TestDiscardPartialRemovesEmptyMountpoint(t *testing.T) {
	useTempExportsConfig(t)
	mp := filepath.Join(t.TempDir(), "osb2-workspace-1-pvc-a")
	if err := os.Mkdir(mp, 0777); err != nil {
		t.Fatal(err)
	}
	writeFile(t, mp+".quota", "image")

	if err := discardPartial(mp); err != nil {
		t.Fatalf("discardPartial: %v", err)
	}
	if exists(mp) || exists(mp+".quota") {
		t.Errorf("leftovers remain: mountpoint %v, quota %v", exists(mp), exists(mp+".quota"))
	}
}

func TestDiscardPartialKeepsNonEmptyDirectory(t *testing.T) {
	useTempExportsConfig(t)
	mp := filepath.Join(t.TempDir(), "osb2-workspace-1-pvc-a")
	if err := os.Mkdir(mp, 0777); err != nil {
		t.Fatal(err)
	}
	data := filepath.Join(mp, "data")
	writeFile(t, data, "user data")

	if err := discardPartial(mp); err == nil {
		t.Fatal("discardPartial on a non-empty directory succeeded, want an error")
	}
	if !exists(data) {
		t.Error("discardPartial deleted data inside the mountpoint")
	}
}

func TestDiscardPartialWithNothingLeft(t *testing.T) {
	useTempExportsConfig(t)
	if err := discardPartial(filepath.Join(t.TempDir(), "osb2-workspace-1-pvc-a")); err != nil {
		t.Fatalf("discardPartial: %v", err)
	}
}

// The watchdog runs every 30 s and used to mount any quota file without a
// mounted directory, including one mkfs was still writing for Create.
func TestRemountIfStaleSkipsVolumeWithoutMountpointDir(t *testing.T) {
	f := newFakeSystem(t)

	missing := f.volume("missing")
	writeFile(t, missing+".quota", "")
	if err := RemountIfStale(missing); err != nil {
		t.Errorf("RemountIfStale(missing mountpoint) = %v, want nil", err)
	}
	if exists(missing) {
		t.Error("RemountIfStale created the mountpoint of a volume being provisioned")
	}

	fileMp := f.volume("file")
	writeFile(t, fileMp, "image")
	writeFile(t, fileMp+".quota", "")
	if err := RemountIfStale(fileMp); err != nil {
		t.Errorf("RemountIfStale(file at mountpoint) = %v, want nil", err)
	}
	if n := f.mountCount(); n != 0 {
		t.Errorf("watchdog mounted %d volumes, want none", n)
	}
}
