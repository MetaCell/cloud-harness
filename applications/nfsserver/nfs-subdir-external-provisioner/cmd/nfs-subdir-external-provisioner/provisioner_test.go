package main

import (
	"os"
	"path/filepath"
	"testing"
)

// kubectl delete pvc: Delete must not skip a volume that still has anything on
// disk. In particular, `nfsvol delete` interrupted after removing the mountpoint
// but before renaming the .quota file onto it leaves only the .quota; skipping
// then deleted the PV and orphaned the volume.
func TestVolumeExists(t *testing.T) {
	for name, tc := range map[string]struct {
		setup func(t *testing.T, mp string)
		want  bool
	}{
		"nothing on disk": {
			setup: func(*testing.T, string) {},
			want:  false,
		},
		"provisioned volume": {
			setup: func(t *testing.T, mp string) {
				mkdir(t, mp)
				touch(t, mp+".quota")
			},
			want: true,
		},
		"delete interrupted before renaming the quota file": {
			setup: func(t *testing.T, mp string) { touch(t, mp+".quota") },
			want:  true,
		},
		"image awaiting archive": {
			setup: func(t *testing.T, mp string) { touch(t, mp) },
			want:  true,
		},
	} {
		t.Run(name, func(t *testing.T) {
			mp := filepath.Join(t.TempDir(), "osb2-workspace-1-pvc-0000")
			tc.setup(t, mp)
			if got := volumeExists(mp); got != tc.want {
				t.Errorf("volumeExists = %v, want %v", got, tc.want)
			}
		})
	}
}

func mkdir(t *testing.T, path string) {
	t.Helper()
	if err := os.Mkdir(path, 0777); err != nil {
		t.Fatal(err)
	}
}

func touch(t *testing.T, path string) {
	t.Helper()
	if err := os.WriteFile(path, nil, 0644); err != nil {
		t.Fatal(err)
	}
}
