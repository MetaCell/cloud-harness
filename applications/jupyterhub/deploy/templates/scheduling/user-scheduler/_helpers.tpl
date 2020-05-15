{{- /*
Renders the kube-scheduler's image based on .Values.apps.jupyterhub.scheduling.userScheduler.name and
optionally on .Values.apps.jupyterhub.scheduling.userScheduler.tag. The default tag is set to the clusters
kubernetes version.
*/}}
{{- define "jupyterhub.scheduler.image" -}}
{{- $name := .Values.apps.jupyterhub.scheduling.userScheduler.image.name -}}
{{- $valuesVersion := .Values.apps.jupyterhub.scheduling.userScheduler.image.tag -}}
{{- $clusterVersion := (split "-" .Capabilities.KubeVersion.GitVersion)._0 -}}
{{- $tag := $valuesVersion | default $clusterVersion -}}
{{ $name }}:{{ $tag }}
{{- end }}
