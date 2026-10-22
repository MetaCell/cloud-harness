package mount

import (
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
)

// useTempExportsConfig points exportsConfigDir at a fresh temp dir for the test.
func useTempExportsConfig(t *testing.T) string {
	t.Helper()
	old := exportsConfigDir
	exportsConfigDir = t.TempDir()
	t.Cleanup(func() { exportsConfigDir = old })
	return exportsConfigDir
}

func writeFile(t *testing.T, path, content string) {
	t.Helper()
	if err := os.WriteFile(path, []byte(content), 0644); err != nil {
		t.Fatal(err)
	}
}

func TestRegenerateExportsSkipsNonDirectories(t *testing.T) {
	cfg := useTempExportsConfig(t)
	exports := t.TempDir()
	good := filepath.Join(exports, "osb2-good-pvc-1")
	fileMp := filepath.Join(exports, "osb2-file-pvc-2")
	missing := filepath.Join(exports, "osb2-missing-pvc-3")

	if err := os.Mkdir(good, 0777); err != nil {
		t.Fatal(err)
	}
	writeFile(t, fileMp, "ext4 image")
	for _, mp := range []string{good, fileMp, missing} {
		writeFile(t, mp+".quota", "")
	}
	// Stale fragments from a previous incarnation of the pod.
	writeFile(t, pvExportFile(filepath.Base(fileMp)), fileMp+" *(rw)\n")
	writeFile(t, filepath.Join(cfg, "osb2-gone-pvc-4.exports"), "/exports/osb2-gone-pvc-4 *(rw)\n")

	if err := RegenerateExportsFromQuotas(exports); err != nil {
		t.Fatalf("RegenerateExportsFromQuotas: %v", err)
	}

	got, _ := filepath.Glob(filepath.Join(cfg, "*.exports"))
	want := []string{pvExportFile(filepath.Base(good))}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("fragments = %v, want %v", got, want)
	}
	data, err := os.ReadFile(want[0])
	if err != nil {
		t.Fatal(err)
	}
	if !strings.HasPrefix(string(data), good+" ") {
		t.Errorf("fragment = %q, want it to export %s", data, good)
	}
}

func TestIsExported(t *testing.T) {
	old := etabPath
	etabPath = filepath.Join(t.TempDir(), "etab")
	t.Cleanup(func() { etabPath = old })

	if isExported("/exports/osb2-a-pvc-1") {
		t.Error("isExported with no etab = true, want false")
	}

	writeFile(t, etabPath, "/exports\t*(rw,fsid=0)\n/exports/osb2-a-pvc-1\t*(rw,fsid=12)\n")
	for path, want := range map[string]bool{
		"/exports/osb2-a-pvc-1":  true,
		"/exports/osb2-a-pvc-1/": true,
		"/exports/osb2-a":        false,
		"/exports/osb2-b-pvc-2":  false,
	} {
		if got := isExported(path); got != want {
			t.Errorf("isExported(%q) = %v, want %v", path, got, want)
		}
	}
}
