package main

import (
	"flag"
	"fmt"
	"log"
	"os"

	"metacell/nfsvol/internal/mount"
	"metacell/nfsvol/internal/watchdog"
)

const exportsDir = "/exports"

func main() {
	log.SetFlags(log.Ltime | log.Lmicroseconds)

	if len(os.Args) < 2 {
		usage()
		os.Exit(1)
	}

	switch os.Args[1] {
	case "mount-all":
		if err := mount.MountAll(exportsDir); err != nil {
			log.Fatalf("mount-all: %v", err)
		}

	case "create":
		fs := flag.NewFlagSet("create", flag.ExitOnError)
		mountpoint := fs.String("m", "", "mountpoint path (required)")
		size := fs.Int64("s", 0, "size in bytes (required)")
		_ = fs.Parse(os.Args[2:])
		if *mountpoint == "" || *size == 0 {
			fmt.Fprintln(os.Stderr, "create: -m <path> and -s <bytes> are required")
			os.Exit(1)
		}
		if err := mount.Create(*mountpoint, *size); err != nil {
			log.Fatalf("create %s: %v", *mountpoint, err)
		}

	case "delete":
		fs := flag.NewFlagSet("delete", flag.ExitOnError)
		mountpoint := fs.String("m", "", "mountpoint path (required)")
		_ = fs.Parse(os.Args[2:])
		if *mountpoint == "" {
			fmt.Fprintln(os.Stderr, "delete: -m <path> is required")
			os.Exit(1)
		}
		if err := mount.Delete(*mountpoint); err != nil {
			log.Fatalf("delete %s: %v", *mountpoint, err)
		}

	case "watchdog":
		fs := flag.NewFlagSet("watchdog", flag.ExitOnError)
		interval := fs.Int("interval", 30, "check interval in seconds")
		addr := fs.String("addr", ":8080", "healthz listen address")
		_ = fs.Parse(os.Args[2:])
		watchdog.Run(exportsDir, *interval, *addr)

	default:
		usage()
		os.Exit(1)
	}
}

func usage() {
	fmt.Fprintf(os.Stderr, `Usage: nfsvol <command> [flags]

Commands:
  mount-all
        Mount all *.quota files under /exports in parallel (bootstrap).

  create -m <path> -s <bytes>
        Create and mount a new quota-backed directory.

  delete -m <path>
        Unmount and clean up a quota-backed directory.

  watchdog [-interval <s>] [-addr <addr>]
        Long-running health monitor that remounts stale volumes and exposes
        a /healthz endpoint (default :8080).
`)
}
