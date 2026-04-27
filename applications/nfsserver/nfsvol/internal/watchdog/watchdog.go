package watchdog

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"sync"
	"sync/atomic"
	"syscall"
	"time"

	"metacell/nfsvol/internal/mount"
)

// Run starts the mount health watchdog and a /healthz HTTP endpoint.
// It blocks until SIGTERM or SIGINT is received.
func Run(exportsDir string, intervalSecs int, addr string) {
	var healthy atomic.Int32
	healthy.Store(1)

	mux := http.NewServeMux()
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		if healthy.Load() == 1 {
			w.WriteHeader(http.StatusOK)
			fmt.Fprintln(w, "ok")
		} else {
			w.WriteHeader(http.StatusServiceUnavailable)
			fmt.Fprintln(w, "unhealthy")
		}
	})

	srv := &http.Server{Addr: addr, Handler: mux}
	go func() {
		log.Printf("watchdog: healthz listening on %s", addr)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Printf("watchdog: http server: %v", err)
		}
	}()

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, syscall.SIGINT)
	defer stop()

	ticker := time.NewTicker(time.Duration(intervalSecs) * time.Second)
	defer ticker.Stop()

	log.Printf("watchdog: started, interval=%ds, exports=%s", intervalSecs, exportsDir)

	for {
		select {
		case <-ctx.Done():
			_ = srv.Shutdown(context.Background())
			return
		case <-ticker.C:
			if ok := checkAll(exportsDir); ok {
				healthy.Store(1)
			} else {
				healthy.Store(0)
			}
		}
	}
}

// checkAll verifies and repairs all expected mountpoints concurrently.
// Returns true if all mounts are healthy after the check.
func checkAll(exportsDir string) bool {
	quotaFiles, err := filepath.Glob(filepath.Join(exportsDir, "*.quota"))
	if err != nil || len(quotaFiles) == 0 {
		return true
	}

	var wg sync.WaitGroup
	var failures atomic.Int32

	for _, qf := range quotaFiles {
		mp := strings.TrimSuffix(qf, ".quota")
		wg.Add(1)
		go func(mountpoint string) {
			defer wg.Done()
			if err := mount.RemountIfStale(mountpoint); err != nil {
				log.Printf("watchdog: remount failed for %s: %v", mountpoint, err)
				failures.Add(1)
			}
		}(mp)
	}
	wg.Wait()

	if n := failures.Load(); n > 0 {
		log.Printf("watchdog: %d/%d mounts still unhealthy", n, len(quotaFiles))
		return false
	}

	// Ensure /exports itself is accessible (basic NFS server sanity check).
	if _, err := os.Stat(exportsDir); err != nil {
		log.Printf("watchdog: exports dir inaccessible: %v", err)
		return false
	}
	return true
}
