{{/* vim: set filetype=mustache: */}}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "deploy_utils.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{/*
For custom images: if images are coming from local(e.g minikube) registry, image pull policy is "Never". Otherwise it is "IfNotPresent"
*/}}
{{- define "deploy_utils.pullpolicy" -}}
{{- if and .Values.local (not .Values.registry.name) -}}
{{- print "Never" -}}
{{- else -}}
{{- print "IfNotPresent" -}}
{{- end -}}
{{- end -}}
{{/*
Add environmental variables to all containers
*/}}
{{- define "deploy_utils.env" -}}
{{- range $pair := .Values.env }}
- name: {{ $pair.name | quote }}
  value: {{ $pair.value | quote }}
{{- end }}
{{- if .Values.apps.accounts }}
- name: CH_ACCOUNTS_CLIENT_SECRET
  value: {{ .Values.apps.accounts.client.secret | quote }}
- name: CH_ACCOUNTS_REALM
  value: {{ .Values.namespace | quote }}
- name: CH_ACCOUNTS_AUTH_DOMAIN
  value: {{ printf "%s.%s" .Values.apps.accounts.harness.subdomain .Values.domain | quote }}
- name: CH_ACCOUNTS_CLIENT_ID
  value: {{ .Values.apps.accounts.client.id | quote }}
- name: DOMAIN
  value: {{ .Values.domain | quote }}
{{- end -}}
{{- end -}}
{{/*
Add private environmental variables to all containers
*/}}
{{- define "deploy_utils.privenv" -}}
{{- range $env := .Values.privenv }}
- name: {{ $env.name | quote }}
  valueFrom:
    secretKeyRef:
      name: deployment-secrets
      key: {{ $env.name | quote }}
{{- end }}
{{- end -}}
{{/*
Defines docker registry
*/}}
{{- define "deploy_utils.registry" }}
{{- if not (eq .Values.registry.name "") }}
{{- printf "%s" .Values.registry.name }}
{{- end }}
{{- end }}

{{/* Create chart name and version as used by the chart label. */}}
{{- define "deploy_utils.chartref" -}}
{{- replace "+" "_" $.Chart.Version | printf "%s-%s" $.Chart.Name -}}
{{- end }}

{{/* Generate basic labels */}}
{{- define "deploy_utils.labels" }}
chart: {{ template "deploy_utils.chartref" . }}
release: {{ $.Release.Name | quote }}
heritage: {{ $.Release.Service | quote }}
{{- if .Values.commonLabels}}
{{ toYaml .Values.commonLabels }}
{{- end }}
{{- end }}


{{/* /etc/hosts */}}
{{- define "deploy_utils.etcHosts" }}
{{- if .Values.local }}
{{ $domain := .Values.domain }}
hostAliases:
  - ip: {{ .Values.localIp }}
    hostnames:
    {{ printf "- %s" .Values.domain }}
    {{- range $app := .Values.apps }}
    {{- if $app.harness.subdomain }}
    {{ printf "- %s.%s" $app.harness.subdomain $domain }}
    {{- end }}
    {{- end }}
{{- end }}
{{- end }}
