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

const checkWorkers = 32

// Run starts the mount health watchdog and HTTP endpoints.
// It blocks until SIGTERM or SIGINT is received.
//
// If mountFirst is true, MountAll is run synchronously before the watch
// loop starts. The HTTP server is up throughout so the liveness probe is
// satisfied immediately; the readiness probe (/ready) only returns 200 once
// MountAll completes.
func Run(exportsDir string, intervalSecs int, addr string, mountFirst bool) {
	var ready atomic.Int32 // 0 = starting, 1 = ready

	mux := http.NewServeMux()

	// /healthz: liveness — always 200 while the process is running.
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		fmt.Fprintln(w, "ok")
	})

	// /ready: readiness — 200 only after mount-all completes.
	mux.HandleFunc("/ready", func(w http.ResponseWriter, r *http.Request) {
		if ready.Load() == 1 {
			w.WriteHeader(http.StatusOK)
			fmt.Fprintln(w, "ready")
		} else {
			w.WriteHeader(http.StatusServiceUnavailable)
			fmt.Fprintln(w, "starting")
		}
	})

	srv := &http.Server{Addr: addr, Handler: mux}
	go func() {
		log.Printf("watchdog: listening on %s", addr)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Printf("watchdog: http server: %v", err)
		}
	}()

	if mountFirst {
		log.Printf("watchdog: running mount-all")
		if err := mount.MountAll(exportsDir); err != nil {
			log.Printf("watchdog: mount-all failed: %v", err)
		}
	}
	ready.Store(1)

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
			checkAll(exportsDir)
		}
	}
}

// checkAll verifies and repairs all expected mountpoints via a bounded worker pool.
func checkAll(exportsDir string) bool {
	quotaFiles, err := filepath.Glob(filepath.Join(exportsDir, "*.quota"))
	if err != nil || len(quotaFiles) == 0 {
		return true
	}

	type job struct{ mountpoint string }
	jobs := make(chan job, len(quotaFiles))
	for _, qf := range quotaFiles {
		jobs <- job{strings.TrimSuffix(qf, ".quota")}
	}
	close(jobs)

	var wg sync.WaitGroup
	var failures atomic.Int32

	workers := checkWorkers
	if workers > len(quotaFiles) {
		workers = len(quotaFiles)
	}
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := range jobs {
				if err := mount.RemountIfStale(j.mountpoint); err != nil {
					log.Printf("watchdog: remount failed for %s: %v", j.mountpoint, err)
					failures.Add(1)
				}
			}
		}()
	}
	wg.Wait()

	if n := failures.Load(); n > 0 {
		log.Printf("watchdog: %d/%d mounts still unhealthy", n, len(quotaFiles))
		return false
	}

	if _, err := os.Stat(exportsDir); err != nil {
		log.Printf("watchdog: exports dir inaccessible: %v", err)
		return false
	}
	return true
}
