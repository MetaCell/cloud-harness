package mount

import (
	"crypto/sha256"
	"encoding/binary"
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// Directory scanned by rpc.mountd for fragment exports files.
// Variables rather than constants so tests can point them at a temp dir.
var exportsConfigDir = "/etc/exports.d"

// Table of active exports, rewritten by every `exportfs` run.
var etabPath = "/var/lib/nfs/etab"

// fsidFromPVName derives a stable uint32 NFS fsid from the given PV name.
// 0 and 1 are reserved by NFS (0 = NFSv4 pseudo-root, 1 = unused) so values
// in that range are bumped out of the reserved zone.
//
// Collision probability with SHA-256 → 32-bit is ~N²/2^33, which is
// ~2×10⁻⁵ at N=10⁴ and ~1×10⁻¹ at N=10⁶. If the provisioner ever needs to
// handle >10⁴ active PVCs, switch to NFSv4 `fsid=<uuid>` syntax.
func fsidFromPVName(pvName string) uint32 {
	h := sha256.Sum256([]byte(pvName))
	fsid := binary.BigEndian.Uint32(h[:4])
	if fsid < 2 {
		fsid += 2
	}
	return fsid
}

// pvExportFile returns the /etc/exports.d/ fragment path for a given PV name.
func pvExportFile(pvName string) string {
	return filepath.Join(exportsConfigDir, pvName+".exports")
}

// WriteExport writes (or replaces) the exports fragment for a mountpoint with
// a deterministic fsid so client file handles remain valid across server
// restarts, pod reschedules, and watchdog remounts.
func WriteExport(mountpoint string) error {
	pvName := filepath.Base(mountpoint)
	fsid := fsidFromPVName(pvName)

	if err := os.MkdirAll(exportsConfigDir, 0755); err != nil {
		return fmt.Errorf("mkdir %s: %w", exportsConfigDir, err)
	}

	contents := fmt.Sprintf(
		"%s *(rw,fsid=%d,insecure,no_subtree_check,no_root_squash)\n",
		mountpoint, fsid,
	)

	dst := pvExportFile(pvName)
	tmp := dst + ".tmp"
	if err := os.WriteFile(tmp, []byte(contents), 0644); err != nil {
		return fmt.Errorf("write %s: %w", tmp, err)
	}
	if err := os.Rename(tmp, dst); err != nil {
		_ = os.Remove(tmp)
		return fmt.Errorf("rename %s → %s: %w", tmp, dst, err)
	}
	return nil
}

// RemoveExport removes the exports fragment for a mountpoint. Idempotent.
func RemoveExport(mountpoint string) error {
	pvName := filepath.Base(mountpoint)
	if err := os.Remove(pvExportFile(pvName)); err != nil && !os.IsNotExist(err) {
		return err
	}
	return nil
}

// runExportfs runs `exportfs -r`; a variable so tests can replace it.
var runExportfs = func() ([]byte, error) {
	return exec.Command("exportfs", "-r").CombinedOutput()
}

// ReloadExports has the kernel re-read /etc/exports and /etc/exports.d/.
// Safe to call whether or not rpc.mountd is running yet.
func ReloadExports() error {
	if out, err := runExportfs(); err != nil {
		return fmt.Errorf("exportfs -r: %w\n%s", err, out)
	}
	return nil
}

// reloadExportsFor runs ReloadExports and succeeds if mountpoint ends up in the
// active export table even when exportfs exits non-zero. exportfs only warns
// about a bad entry (e.g. a path that is not a directory), still writes etab and
// flushes the kernel cache, then exits 1 — so a bad fragment belonging to some
// other volume must not fail operations on this one.
func reloadExportsFor(mountpoint string) error {
	err := ReloadExports()
	if err == nil || !isExported(mountpoint) {
		return err
	}
	log.Printf("%s is exported; ignoring exportfs failure: %v", mountpoint, err)
	return nil
}

// isExported reports whether path is listed in the active export table.
func isExported(path string) bool {
	data, err := os.ReadFile(etabPath)
	if err != nil {
		return false
	}
	path = filepath.Clean(path)
	for _, line := range strings.Split(string(data), "\n") {
		if f := strings.Fields(line); len(f) > 0 && f[0] == path {
			return true
		}
	}
	return false
}

// RegenerateExportsFromQuotas rewrites /etc/exports.d/ to match the set of
// *.quota files under exportsBase, removing fragments for volumes that no
// longer exist. Used by mount-all at startup to converge the exports table
// with reality — crucial after a node reschedule where the previous pod's
// exports.d may have stale entries (or none at all, on a fresh node).
func RegenerateExportsFromQuotas(exportsBase string) error {
	quotaFiles, err := filepath.Glob(filepath.Join(exportsBase, "*.quota"))
	if err != nil {
		return err
	}

	wanted := make(map[string]bool, len(quotaFiles))
	for _, qf := range quotaFiles {
		mp := strings.TrimSuffix(qf, ".quota")
		// Export only directories. A single fragment for a missing path or a
		// regular file (left by a failed Create) makes every `exportfs -r`
		// exit non-zero. Leaving it out of `wanted` also drops a stale one.
		if !isDir(mp) {
			log.Printf("mount-all: not exporting %s: not a directory", mp)
			continue
		}
		pvName := filepath.Base(mp)
		wanted[pvExportFile(pvName)] = true
		if err := WriteExport(mp); err != nil {
			log.Printf("mount-all: write export for %s: %v", mp, err)
		}
	}

	existing, err := filepath.Glob(filepath.Join(exportsConfigDir, "*.exports"))
	if err != nil {
		return nil // directory may not exist yet; WriteExport would have created it
	}
	for _, e := range existing {
		if !wanted[e] {
			if err := os.Remove(e); err != nil {
				log.Printf("mount-all: remove stale export %s: %v", e, err)
			}
		}
	}
	return nil
}
