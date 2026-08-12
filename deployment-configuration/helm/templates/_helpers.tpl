{{/* vim: set filetype=mustache: */}}

{{/*
Render resources block for deployment, omitting limits if not set
Usage: {{ include "deploy_utils.resources" .app.harness.deployment.resources }}
*/}}
{{- define "deploy_utils.resources" -}}
resources:
  requests:
    {{- if .requests.memory }}
    memory: {{ .requests.memory }}
    {{- end }}
    {{- if .requests.cpu }}
    cpu: {{ .requests.cpu }}
    {{- end }}
  {{- if or .limits.memory .limits.cpu }}
  limits:
    {{- if .limits.memory }}
    memory: {{ .limits.memory }}
    {{- end }}
    {{- if .limits.cpu }}
    cpu: {{ .limits.cpu }}
    {{- end }}
  {{- end }}
{{- end -}}

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
{{- print "IfNotPresent" -}}
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


{{/*
Render volumeMounts block for a container.
Usage: {{ include "deploy_utils.volumeMounts" (dict "app" .app "root" .root) }}
*/}}
{{- define "deploy_utils.volumeMounts" -}}
volumeMounts:
  - name: cloudharness-allvalues
    mountPath: /opt/cloudharness/resources
    readOnly: true
  {{- $root := .root }}
  {{- range $dep := concat .app.harness.dependencies.hard .app.harness.dependencies.soft }}
  {{- $depApp := index $root.Values.apps $dep }}
  {{- if $depApp.harness.secrets }}
  - name: cloudharness-{{ $dep }}
    mountPath: /opt/cloudharness/resources/secrets/{{ $dep }}
    readOnly: true
  {{- end }}
  {{- end }}
  {{- if (has  "accounts" .app.harness.dependencies.hard) }}
  {{/* legacy path for accounts auth resources mount */}}
  - name: cloudharness-accounts
    mountPath: /opt/cloudharness/resources/auth
    readOnly: true
  {{- end }}
  {{- if  .app.harness.deployment.volume }}
  - name: {{ .app.harness.deployment.volume.name }}
    mountPath: {{ .app.harness.deployment.volume.mountpath }}
    readOnly: {{ .app.harness.deployment.volume.readonly | default false }}
  {{- end }}
  {{- $app := .app}}
  {{- range $resource := .app.harness.resources }}
  - name: "{{ $app.harness.deployment.name }}-{{ $resource.name }}"
    mountPath: {{ $resource.dst }}
    subPath: {{ base $resource.dst }}
    readOnly: true
  {{- end}}
  {{- if .app.harness.secrets }}
  - name: secrets
    mountPath: "/opt/cloudharness/resources/secrets/{{ .app.harness.name }}"
    readOnly: true
  {{- end }}
  {{- if kindIs "map" .app.harness.database }}
    {{- if and (hasKey .app.harness.database "connect_string") .app.harness.database.connect_string }}
  - name: db-external
    mountPath: "/opt/cloudharness/resources/db"
    readOnly: true
    {{- end }}
  {{- end }}
{{- end -}}

{{/*
Render a single extra container spec (init container or sidecar).
Usage: {{ include "deploy_utils.extraContainerSpec" (dict "name" $name "container" $container "app" .app "root" .root) }}
*/}}
{{- define "deploy_utils.extraContainerSpec" -}}
- name: {{ .name | quote }}
  image: {{ .container.image | default .app.harness.deployment.image }}
  imagePullPolicy: {{ include "deploy_utils.pullpolicy" .root }}
  {{- if .container.command }}
  command:
    {{- .container.command | toYaml | nindent 4 }}
  {{- end }}
  env:
  - name: CH_CURRENT_APP_NAME
    value: {{ .app.harness.name | quote }}
    {{- include "deploy_utils.env" .root | nindent 2 }}
    {{- include "deploy_utils.privenv" .root | nindent 2 }}
    {{- if .app.harness.env }}
    {{- .app.harness.env | toYaml | nindent 2 }}
    {{- end }}
    {{- range $name, $value := .app.harness.envmap }}
  - name: {{ $name | quote }}
    value: {{ $value | quote }}
    {{- end }}
  {{- if dig "resources" "requests" nil .container }}
  {{- include "deploy_utils.resources" .container.resources | nindent 2 }}
  {{- else }}
  {{- include "deploy_utils.resources" .app.harness.deployment.resources | nindent 2 }}
  {{- end }}
  {{- if .container.shareVolume }}
  {{- include "deploy_utils.volumeMounts" (dict "app" .app "root" .root) | nindent 2 }}
  {{- end }}
{{- end -}}

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
