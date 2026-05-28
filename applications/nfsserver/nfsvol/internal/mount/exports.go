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
const exportsConfigDir = "/etc/exports.d"

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

// ReloadExports has the kernel re-read /etc/exports and /etc/exports.d/.
// Safe to call whether or not rpc.mountd is running yet.
func ReloadExports() error {
	cmd := exec.Command("exportfs", "-r")
	if out, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("exportfs -r: %w\n%s", err, out)
	}
	return nil
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
