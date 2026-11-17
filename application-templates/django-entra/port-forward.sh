fuser -k 5432/tcp
namespace=${1:-ch}
echo "Port forwarding for $namespace"
kubectl port-forward --namespace $namespace deployment/__APP_NAME__-db 5432:5432 &
