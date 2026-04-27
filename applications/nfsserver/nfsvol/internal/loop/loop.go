package loop

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"golang.org/x/sys/unix"
)

const loopControlPath = "/dev/loop-control"

// GetFree returns the index of the next free loop device as allocated by the kernel.
// The kernel atomically reserves the device so concurrent callers get distinct indices.
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
	n, err := GetFree()
	if err != nil {
		return "", err
	}
	if err := EnsureDevice(n); err != nil {
		return "", fmt.Errorf("ensure device loop%d: %w", n, err)
	}
	loopPath := DevPath(n)

	bf, err := os.OpenFile(backingFile, os.O_RDWR, 0)
	if err != nil {
		return "", fmt.Errorf("open backing file %s: %w", backingFile, err)
	}
	defer bf.Close()

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

// FindByBacking returns the loop device path for the given backing file by scanning
// /sys/block/loop*/loop/backing_file. Returns "" if none is found.
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
		// The kernel appends " (deleted)" for files still open but unlinked.
		backing = strings.TrimSuffix(backing, " (deleted)")
		if backing == abs {
			// /sys/block/loop7/loop/backing_file → /dev/loop7
			parts := strings.Split(entry, "/")
			return "/dev/" + parts[3], nil
		}
	}
	return "", nil
}

// DetachByBacking finds and detaches the loop device backing the given file.
// It is a no-op if no loop device is associated with the file.
func DetachByBacking(backingFile string) error {
	loopPath, err := FindByBacking(backingFile)
	if err != nil || loopPath == "" {
		return err
	}
	return Detach(loopPath)
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
