{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "nfs-subdir-external-provisioner.name" -}}
{{- default .Chart.Name .Values.apps.nfsserver.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "nfs-subdir-external-provisioner.fullname" -}}
{{- if .Values.apps.nfsserver.fullnameOverride -}}
{{- .Values.apps.nfsserver.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.apps.nfsserver.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "nfs-subdir-external-provisioner.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "nfs-subdir-external-provisioner.provisionerName" -}}
{{- if .Values.apps.nfsserver.storageClass.provisionerName -}}
{{- printf .Values.apps.nfsserver.storageClass.provisionerName -}}
{{- else -}}
{{ template "nfs-subdir-external-provisioner.fullname" . -}}
{{- end -}}
{{- end -}}

{{/*
Create the name of the service account to use
*/}}
{{- define "nfs-subdir-external-provisioner.serviceAccountName" -}}
{{- if .Values.apps.nfsserver.serviceAccount.create -}}
    {{ default (include "nfs-subdir-external-provisioner.fullname" .) .Values.apps.nfsserver.serviceAccount.name }}
{{- else -}}
    {{ default "default" .Values.apps.nfsserver.serviceAccount.name }}
{{- end -}}
{{- end -}}

{{/*
Return the appropriate apiVersion for podSecurityPolicy.
*/}}
{{- define "podSecurityPolicy.apiVersion" -}}
{{- if semverCompare ">=1.10-0" .Capabilities.KubeVersion.GitVersion -}}
{{- print "policy/v1beta1" -}}
{{- else -}}
{{- print "extensions/v1beta1" -}}
{{- end -}}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "nfs-subdir-external-provisioner.labels" -}}
chart: {{ template "nfs-subdir-external-provisioner.chart" . }}
heritage: {{ .Release.Service }}
{{ include "nfs-subdir-external-provisioner.selectorLabels" . }}
{{- with .Values.apps.nfsserver.labels }}
{{- toYaml . | nindent 0 }}
{{- end }}
{{- end }}

{{/*
Pod template labels
*/}}
{{- define "nfs-subdir-external-provisioner.podLabels" -}}
{{ include "nfs-subdir-external-provisioner.selectorLabels" . }}
{{- with .Values.apps.nfsserver.labels }}
{{- toYaml . | nindent 0 }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "nfs-subdir-external-provisioner.selectorLabels" -}}
app: {{ template "nfs-subdir-external-provisioner.name" . }}
release: {{ .Release.Name }}
{{- end }}
