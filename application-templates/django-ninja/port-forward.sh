fuser -k 5432/tcp
fuser -k 8080/tcp
namespace=${1:-ch}
echo "Port forwarding for $namespace"
kubectl port-forward --namespace $namespace deployment/accounts 8080:8080 &
kubectl port-forward --namespace $namespace deployment/__APP_NAME__-db 5432:5432 &
