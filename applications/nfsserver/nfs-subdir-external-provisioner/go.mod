module github.com/kubernetes-sigs/nfs-subdir-external-provisioner

go 1.24.0

require (
	github.com/golang/glog v1.2.5
	k8s.io/api v0.23.17
	k8s.io/apimachinery v0.23.17
	k8s.io/client-go v0.23.17
	k8s.io/component-helpers v0.23.17
	sigs.k8s.io/sig-storage-lib-external-provisioner/v6 v6.0.0
)

require (
	github.com/beorn7/perks v1.0.1 // indirect
	github.com/cespare/xxhash/v2 v2.3.0 // indirect
	github.com/davecgh/go-spew v1.1.2-0.20180830191138-d8f796af33cc // indirect
	github.com/go-logr/logr v1.4.3 // indirect
	github.com/gogo/protobuf v1.3.2 // indirect
	github.com/golang/groupcache v0.0.0-20241129210726-2c02b8208cf8 // indirect
	github.com/golang/protobuf v1.5.4 // indirect
	github.com/google/go-cmp v0.7.0 // indirect
	github.com/google/gofuzz v1.1.0 // indirect
	github.com/google/uuid v1.6.0 // indirect
	github.com/googleapis/gnostic v0.5.5 // indirect
	github.com/imdario/mergo v0.3.5 // indirect
	github.com/json-iterator/go v1.1.12 // indirect
	github.com/miekg/dns v1.1.29 // indirect
	github.com/modern-go/concurrent v0.0.0-20180306012644-bacd9c7ef1dd // indirect
	github.com/modern-go/reflect2 v1.0.2 // indirect
	github.com/munnerz/goautoneg v0.0.0-20191010083416-a7dc8b61c822 // indirect
	github.com/prometheus/client_golang v1.21.1 // indirect
	github.com/prometheus/client_model v0.6.2 // indirect
	github.com/prometheus/common v0.63.0 // indirect
	github.com/prometheus/procfs v0.16.0 // indirect
	github.com/spf13/pflag v1.0.5 // indirect
	golang.org/x/crypto v0.45.0 // indirect
	golang.org/x/net v0.48.0 // indirect
	golang.org/x/oauth2 v0.34.0 // indirect
	golang.org/x/sys v0.39.0 // indirect
	golang.org/x/term v0.37.0 // indirect
	golang.org/x/text v0.32.0 // indirect
	golang.org/x/time v0.11.0 // indirect
	google.golang.org/protobuf v1.36.10 // indirect
	gopkg.in/inf.v0 v0.9.1 // indirect
	gopkg.in/yaml.v2 v2.4.0 // indirect
	gopkg.in/yaml.v3 v3.0.1 // indirect
	k8s.io/klog v1.0.0 // indirect
	k8s.io/klog/v2 v2.30.0 // indirect
	k8s.io/kube-openapi v0.0.0-20211115234752-e816edb12b65 // indirect
	k8s.io/utils v0.0.0-20211116205334-6203023598ed // indirect
	sigs.k8s.io/json v0.0.0-20211020170558-c049b76a60c6 // indirect
	sigs.k8s.io/structured-merge-diff/v4 v4.2.3 // indirect
	sigs.k8s.io/yaml v1.2.0 // indirect
)

replace (
	github.com/elazarl/goproxy => github.com/elazarl/goproxy v0.0.0-20230731152917-f99041a5c027
	github.com/emicklei/go-restful => github.com/emicklei/go-restful v2.16.0+incompatible
	github.com/getkin/kin-openapi => github.com/getkin/kin-openapi v0.131.0
	github.com/prometheus/client_golang => github.com/prometheus/client_golang v1.21.1
	github.com/sirupsen/logrus => github.com/sirupsen/logrus v1.9.3
	golang.org/x/crypto => golang.org/x/crypto v0.45.0
	golang.org/x/image => golang.org/x/image v0.18.0
	golang.org/x/net => golang.org/x/net v0.38.0
	golang.org/x/oauth2 => golang.org/x/oauth2 v0.27.0
	golang.org/x/text => golang.org/x/text v0.3.8
	google.golang.org/grpc => google.golang.org/grpc v1.79.3
	gopkg.in/yaml.v3 => gopkg.in/yaml.v3 v3.0.1
	k8s.io/api => k8s.io/api v0.23.17
	k8s.io/apiextensions-apiserver => k8s.io/apiextensions-apiserver v0.23.17
	k8s.io/apimachinery => k8s.io/apimachinery v0.23.17
	k8s.io/apiserver => k8s.io/apiserver v0.23.17
	k8s.io/cli-runtime => k8s.io/cli-runtime v0.23.17
	k8s.io/client-go => k8s.io/client-go v0.23.17
	k8s.io/cloud-provider => k8s.io/cloud-provider v0.23.17
	k8s.io/cluster-bootstrap => k8s.io/cluster-bootstrap v0.23.17
	k8s.io/code-generator => k8s.io/code-generator v0.23.17
	k8s.io/component-base => k8s.io/component-base v0.23.17
	k8s.io/component-helpers => k8s.io/component-helpers v0.23.17
	k8s.io/controller-manager => k8s.io/controller-manager v0.23.17
	k8s.io/cri-api => k8s.io/cri-api v0.23.17
	k8s.io/csi-translation-lib => k8s.io/csi-translation-lib v0.23.17
	k8s.io/kube-aggregator => k8s.io/kube-aggregator v0.23.17
	k8s.io/kube-controller-manager => k8s.io/kube-controller-manager v0.23.17
	k8s.io/kube-proxy => k8s.io/kube-proxy v0.23.17
	k8s.io/kube-scheduler => k8s.io/kube-scheduler v0.23.17
	k8s.io/kubectl => k8s.io/kubectl v0.23.17
	k8s.io/kubelet => k8s.io/kubelet v0.23.17
	k8s.io/legacy-cloud-providers => k8s.io/legacy-cloud-providers v0.23.17
	k8s.io/metrics => k8s.io/metrics v0.23.17
	k8s.io/mount-utils => k8s.io/mount-utils v0.23.17
	k8s.io/pod-security-admission => k8s.io/pod-security-admission v0.23.17
	k8s.io/sample-apiserver => k8s.io/sample-apiserver v0.23.17
	k8s.io/sample-cli-plugin => k8s.io/sample-cli-plugin v0.23.17
	k8s.io/sample-controller => k8s.io/sample-controller v0.23.17
)
