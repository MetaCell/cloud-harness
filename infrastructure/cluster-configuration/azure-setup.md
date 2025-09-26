# Azure AKS setup

The main complication within AKS is given by the fact that the nginx ingress controller
is not easy to setup, hence the AGIC controller has to be preferred.


1. Create new public IP for the AGIC load balancer
2. Create the application gateway
3. Enable AGIC add-on in existing AKS cluster with Azure CLI
4. Peer the AKS and AG virtual networks together

See https://learn.microsoft.com/en-us/azure/application-gateway/tutorial-ingress-controller-add-on-existing.

## Adapt / override Ingress template
In addition to this, the [Ingress template](../../deployment-configuration/helm/templates/ingress.yaml) has to be adapted to use the agic controller.

An adaptation to the Ingress controller template that optionally supports AGIC is the following
```yaml
kind: Ingress
metadata:
  name: {{ .Values.ingress.name | quote }}
  annotations:
    {{- if eq .Values.ingress.className "azure-application-gateway" }}
    appgw.ingress.kubernetes.io/backend-path-prefix: /
      {{- if $tls }}
    appgw.ingress.kubernetes.io/appgw-ssl-certificate: "nwwcssl"
      {{- end }}
    appgw.ingress.kubernetes.io/ssl-redirect: {{ (and $tls .Values.ingress.ssl_redirect) | quote }}
    {{- else }}
    nginx.ingress.kubernetes.io/ssl-redirect: {{ (and $tls .Values.ingress.ssl_redirect) | quote }}
    nginx.ingress.kubernetes.io/proxy-body-size: '{{ .Values.proxy.payload.max }}m'
    nginx.ingress.kubernetes.io/proxy-buffer-size: '128k'
    nginx.ingress.kubernetes.io/from-to-www-redirect: 'true'
    nginx.ingress.kubernetes.io/rewrite-target: /$1
    nginx.ingress.kubernetes.io/auth-keepalive-timeout: {{ .Values.proxy.timeout.keepalive | quote }}
    nginx.ingress.kubernetes.io/proxy-read-timeout: {{ .Values.proxy.timeout.read | quote }}
    nginx.ingress.kubernetes.io/proxy-send-timeout: {{ .Values.proxy.timeout.send | quote }}
    nginx.ingress.kubernetes.io/use-forwarded-headers: {{ .Values.proxy.forwardedHeaders | quote }}

    {{- end }}
    {{- if and (and (not .Values.local) (not .Values.certs)) $tls }}
    kubernetes.io/tls-acme: 'true'
    cert-manager.io/issuer: {{ printf "%s-%s" "letsencrypt" .Values.namespace }}
    {{- end }}
```