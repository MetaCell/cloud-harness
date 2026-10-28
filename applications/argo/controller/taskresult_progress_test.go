package controller

import (
	"context"
	"testing"
	"time"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/tools/cache"
	"k8s.io/client-go/util/workqueue"

	wfv1 "github.com/argoproj/argo-workflows/v3/pkg/apis/workflow/v1alpha1"
	"github.com/argoproj/argo-workflows/v3/pkg/client/clientset/versioned/fake"
	"github.com/argoproj/argo-workflows/v3/workflow/common"
)

// Exercise the real informer/watch and work queue, not just the handler's source.
func TestTaskResultProgressEnqueuesWorkflow(t *testing.T) {
	client := fake.NewSimpleClientset()
	queue := workqueue.NewRateLimitingQueue(workqueue.NewItemExponentialFailureRateLimiter(time.Millisecond, time.Millisecond))
	defer queue.ShutDown()
	controller := &WorkflowController{wfclientset: client, managedNamespace: "progress-test", wfQueue: queue}
	informer := controller.newWorkflowTaskResultInformer()
	stop := make(chan struct{})
	defer close(stop)
	go informer.Run(stop)
	if !cache.WaitForCacheSync(stop, informer.HasSynced) {
		t.Fatal("TaskResult informer did not sync")
	}
	results := client.ArgoprojV1alpha1().WorkflowTaskResults("progress-test")
	result := &wfv1.WorkflowTaskResult{
		ObjectMeta: metav1.ObjectMeta{Name: "progress-node", Namespace: "progress-test", Labels: map[string]string{common.LabelKeyWorkflow: "progress-workflow"}},
		NodeResult: wfv1.NodeResult{Progress: "0/4"},
	}
	var err error
	result, err = results.Create(context.Background(), result, metav1.CreateOptions{})
	if err != nil {
		t.Fatal(err)
	}
	assertQueued := func() {
		t.Helper()
		item := make(chan interface{}, 1)
		go func() {
			key, shutdown := queue.Get()
			if !shutdown {
				item <- key
			}
		}()
		select {
		case key := <-item:
			defer queue.Done(key)
			queue.Forget(key)
			if key != "progress-test/progress-workflow" {
				t.Fatalf("unexpected workflow key: %v", key)
			}
		case <-time.After(3 * time.Second):
			t.Fatal("TaskResult change did not enqueue the running workflow")
		}
	}
	assertQueued()
	for _, progress := range []wfv1.Progress{"1/4", "2/4"} {
		result.Progress = progress
		result, err = results.Update(context.Background(), result, metav1.UpdateOptions{})
		if err != nil {
			t.Fatal(err)
		}
		assertQueued()
	}
}
