helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install ingress ingress-nginx/ingress-nginx -f ingress/values.yaml -n kube-system

helm repo add jetstack https://charts.jetstack.io --force-update
helm install \
  cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --version v1.17.2 \
  --set crds.enabled=true


helm install --name cert-manager --namespace cert-manager --version v0.14.0 jetstack/cert-manager --set webhook.enabled=false