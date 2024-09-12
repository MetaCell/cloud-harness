{{- /*
Returns an image-puller daemonset. Two daemonsets will be created like this.
- hook-image-puller: for pre helm upgrade image pulling (lives temporarily)
- continuous-image-puller: for newly added nodes image pulling
*/}}
{{- define "jupyterhub.imagePuller.daemonset" -}}
apiVersion: apps/v1
kind: DaemonSet
metadata:
  {{- if .hook }}
  name: {{ include "jupyterhub.hook-image-puller.fullname" . }}
  {{- else }}
  name: {{ include "jupyterhub.continuous-image-puller.fullname" . }}
  {{- end }}
  labels:
    {{- include "jupyterhub.labels" . | nindent 4 }}
    {{- if .hook }}
    hub.jupyter.org/deletable: "true"
    {{- end }}
  {{- if .hook }}
  annotations:
    {{- /*
    Allows the daemonset to be deleted when the image-awaiter job is completed.
    */}}
    "helm.sh/hook": pre-install,pre-upgrade
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
    "helm.sh/hook-weight": "-10"
  {{- end }}
spec:
  selector:
    matchLabels:
      {{- include "jupyterhub.matchLabels" . | nindent 6 }}
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 100%
  {{- if typeIs "int" .Values.apps.jupyterhub.prePuller.revisionHistoryLimit }}
  revisionHistoryLimit: {{ .Values.apps.jupyterhub.prePuller.revisionHistoryLimit }}
  {{- end }}
  template:
    metadata:
      labels:
        {{- include "jupyterhub.matchLabels" . | nindent 8 }}
      {{- with .Values.apps.jupyterhub.prePuller.annotations }}
      annotations:
        {{- . | toYaml | nindent 8 }}
      {{- end }}
    spec:
      {{- /*
        image-puller pods are made evictable to save on the k8s pods
        per node limit all k8s clusters have and have a higher priority
        than user-placeholder pods that could block an entire node.
      */}}
      {{- if .Values.apps.jupyterhub.scheduling.podPriority.enabled }}
      priorityClassName: {{ include "jupyterhub.image-puller-priority.fullname" . }}
      {{- end }}
      {{- with .Values.apps.jupyterhub.singleuser.nodeSelector }}
      nodeSelector:
        {{- . | toYaml | nindent 8 }}
      {{- end }}
      {{- with concat .Values.apps.jupyterhub.scheduling.userPods.tolerations .Values.apps.jupyterhub.singleuser.extraTolerations .Values.apps.jupyterhub.prePuller.extraTolerations }}
      tolerations:
        {{- . | toYaml | nindent 8 }}
      {{- end }}
      {{- if include "jupyterhub.userNodeAffinityRequired" . }}
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              {{- include "jupyterhub.userNodeAffinityRequired" . | nindent 14 }}
      {{- end }}
      terminationGracePeriodSeconds: 0
      automountServiceAccountToken: false
      {{- with include "jupyterhub.imagePullSecrets" (dict "root" . "image" .Values.apps.jupyterhub.singleuser.image) }}
      imagePullSecrets: {{ . }}
      {{- end }}
      initContainers:
        {{- /* --- Conditionally pull an image all user pods will use in an initContainer --- */}}
        {{- $blockWithIptables := hasKey .Values.apps.jupyterhub.singleuser.cloudMetadata "enabled" | ternary (not .Values.apps.jupyterhub.singleuser.cloudMetadata.enabled) .Values.apps.jupyterhub.singleuser.cloudMetadata.blockWithIptables }}
        {{- if $blockWithIptables }}
        - name: image-pull-metadata-block
          image: {{ .Values.apps.jupyterhub.singleuser.networkTools.image.name }}:{{ .Values.apps.jupyterhub.singleuser.networkTools.image.tag }}
          {{- with .Values.apps.jupyterhub.singleuser.networkTools.image.pullPolicy }}
          imagePullPolicy: {{ . }}
          {{- end }}
          command:
            - /bin/sh
            - -c
            - echo "Pulling complete"
          {{- with .Values.apps.jupyterhub.prePuller.resources }}
          resources:
            {{- . | toYaml | nindent 12 }}
          {{- end }}
          {{- with .Values.apps.jupyterhub.prePuller.containerSecurityContext }}
          securityContext:
            {{- . | toYaml | nindent 12 }}
          {{- end }}
        {{- end }}

        {{- /* --- Pull default image --- */}}
        - name: image-pull-singleuser
          image: {{ .Values.apps.jupyterhub.singleuser.image.name }}:{{ .Values.apps.jupyterhub.singleuser.image.tag }}
          command:
            - /bin/sh
            - -c
            - echo "Pulling complete"
          {{- with .Values.apps.jupyterhub.prePuller.resources }}
          resources:
            {{- . | toYaml | nindent 12 }}
          {{- end }}
          {{- with .Values.apps.jupyterhub.prePuller.containerSecurityContext }}
          securityContext:
            {{- . | toYaml | nindent 12 }}
          {{- end }}

        {{- /* --- Pull extra containers' images --- */}}
        {{- range $k, $container := concat .Values.apps.jupyterhub.singleuser.initContainers .Values.apps.jupyterhub.singleuser.extraContainers }}
        - name: image-pull-singleuser-init-and-extra-containers-{{ $k }}
          image: {{ $container.image }}
          command:
            - /bin/sh
            - -c
            - echo "Pulling complete"
          {{- with $.Values.apps.jupyterhub.prePuller.resources }}
          resources:
            {{- . | toYaml | nindent 12 }}
          {{- end }}
          {{- with $.Values.apps.jupyterhub.prePuller.containerSecurityContext }}
          securityContext:
            {{- . | toYaml | nindent 12 }}
          {{- end }}
        {{- end }}

        {{- /* --- Conditionally pull profileList images --- */}}
        {{- if .Values.apps.jupyterhub.prePuller.pullProfileListImages }}
        {{- range $k, $container := .Values.apps.jupyterhub.singleuser.profileList }}
        {{- /* profile's kubespawner_override */}}
        {{- if $container.kubespawner_override }}
        {{- if $container.kubespawner_override.image }}
        - name: image-pull-singleuser-profilelist-{{ $k }}
          image: {{ $container.kubespawner_override.image }}
          command:
            - /bin/sh
            - -c
            - echo "Pulling complete"
          {{- with $.Values.apps.jupyterhub.prePuller.resources }}
          resources:
            {{- . | toYaml | nindent 12 }}
          {{- end }}
          {{- with $.Values.apps.jupyterhub.prePuller.containerSecurityContext }}
          securityContext:
            {{- . | toYaml | nindent 12 }}
          {{- end }}
        {{- end }}
        {{- end }}
        {{- /* kubespawner_override in profile's profile_options */}}
        {{- if $container.profile_options }}
        {{- range $option, $option_spec := $container.profile_options }}
        {{- if $option_spec.choices }}
        {{- range $choice, $choice_spec := $option_spec.choices }}
        {{- if $choice_spec.kubespawner_override }}
        {{- if $choice_spec.kubespawner_override.image }}
        - name: image-pull-profile-{{ $k }}-option-{{ $option }}-{{ $choice }}
          image: {{ $choice_spec.kubespawner_override.image }}
          command:
            - /bin/sh
            - -c
            - echo "Pulling complete"
          {{- with $.Values.apps.jupyterhub.prePuller.resources }}
          resources:
            {{- . | toYaml | nindent 12 }}
          {{- end }}
          {{- with $.Values.apps.jupyterhub.prePuller.containerSecurityContext }}
          securityContext:
            {{- . | toYaml | nindent 12 }}
        {{- end }}
        {{- end }}
        {{- end }}
        {{- end }}
        {{- end }}
        {{- end }}
        {{- end }}
        {{- end }}
        {{- end }}

        {{- /* --- Pull extra images --- */}}
        {{- range $k, $v := .Values.apps.jupyterhub.prePuller.extraImages }}
        - name: image-pull-{{ $k }}
          image: {{ $v.name }}:{{ $v.tag }}
          command:
            - /bin/sh
            - -c
            - echo "Pulling complete"
          {{- with $.Values.apps.jupyterhub.prePuller.resources }}
          resources:
            {{- . | toYaml | nindent 12 }}
          {{- end }}
          {{- with $.Values.apps.jupyterhub.prePuller.containerSecurityContext }}
          securityContext:
            {{- . | toYaml | nindent 12 }}
          {{- end }}
      {{- end }}
      {{- /* --- EDIT: CLOUDHARNESS pull images --- */}}
      {{- if $.Values.apps.jupyterhub.harness.dependencies.prepull -}}
        {{- range $k, $v := $.Values.apps.jupyterhub.harness.dependencies.prepull }}
        - name: image-pull--{{ $v }}
          image: {{ get ( get $.Values "task-images" ) $v }}
          command:
            - /bin/sh
            - -c
            - echo "Pulling complete"
          {{- with $.Values.apps.jupyterhub.prePuller.resources }}
          resources:
            {{- . | toYaml | nindent 12 }}
          {{- end }}
          {{- with $.Values.apps.jupyterhub.prePuller.containerSecurityContext }}
          securityContext:
            {{- . | toYaml | nindent 12 }}
          {{- end }}
        {{- end }}
      {{- end }}
      {{- /* --- END EDIT: CLOUDHARNESS pull images --- */}}
      containers:
        - name: pause
          image: {{ .Values.apps.jupyterhub.prePuller.pause.image.name }}:{{ .Values.apps.jupyterhub.prePuller.pause.image.tag }}
          {{- with .Values.apps.jupyterhub.prePuller.resources }}
          resources:
            {{- . | toYaml | nindent 12 }}
          {{- end }}
          {{- with .Values.apps.jupyterhub.prePuller.pause.containerSecurityContext }}
          securityContext:
            {{- . | toYaml | nindent 12 }}
          {{- end }}
{{- end }}


{{- /*
    Returns a rendered k8s DaemonSet resource: continuous-image-puller
*/}}
{{- define "jupyterhub.imagePuller.daemonset.continuous" -}}
    {{- $_ := merge (dict "hook" false "componentPrefix" "continuous-") . }}
    {{- include "jupyterhub.imagePuller.daemonset" $_ }}
{{- end }}


{{- /*
    Returns a rendered k8s DaemonSet resource: hook-image-puller
*/}}
{{- define "jupyterhub.imagePuller.daemonset.hook" -}}
    {{- $_ := merge (dict "hook" true "componentPrefix" "hook-") . }}
    {{- include "jupyterhub.imagePuller.daemonset" $_ }}
{{- end }}


{{- /*
    Returns a checksum of the rendered k8s DaemonSet resource: hook-image-puller

    This checksum is used when prePuller.hook.pullOnlyOnChanges=true to decide if
    it is worth creating the hook-image-puller associated resources.
*/}}
{{- define "jupyterhub.imagePuller.daemonset.hook.checksum" -}}
    {{- /*
        We pin componentLabel and Chart.Version as doing so can pin labels
        of no importance if they would change. Chart.Name is also pinned as
        a harmless technical workaround when we compute the checksum.
    */}}
    {{- $_ := merge (dict "componentLabel" "pinned" "Chart" (dict "Name" "jupyterhub" "Version" "pinned")) . -}}
    {{- $yaml := include "jupyterhub.imagePuller.daemonset.hook" $_ }}
    {{- $yaml | sha256sum }}
{{- end }}


{{- /*
    Returns a truthy string or a blank string depending on if the
    hook-image-puller should be installed. The truthy strings are comments
    that summarize the state that led to returning a truthy string.

    - prePuller.hook.enabled must be true
    - if prePuller.hook.pullOnlyOnChanges is true, the checksum of the
      hook-image-puller daemonset must differ since last upgrade
*/}}
{{- define "jupyterhub.imagePuller.daemonset.hook.install" -}}
    {{- if .Values.apps.jupyterhub.prePuller.hook.enabled }}
        {{- if .Values.apps.jupyterhub.prePuller.hook.pullOnlyOnChanges }}
            {{- $new_checksum := include "jupyterhub.imagePuller.daemonset.hook.checksum" . }}
            {{- $k8s_state := lookup "v1" "ConfigMap" .Release.Namespace (include "jupyterhub.hub.fullname" .) | default (dict "data" (dict)) }}
            {{- $old_checksum := index $k8s_state.data "checksum_hook-image-puller" | default "" }}
            {{- if ne $new_checksum $old_checksum -}}
# prePuller.hook.enabled={{ .Values.apps.jupyterhub.prePuller.hook.enabled }}
# prePuller.hook.pullOnlyOnChanges={{ .Values.apps.jupyterhub.prePuller.hook.pullOnlyOnChanges }}
# post-upgrade checksum != pre-upgrade checksum (of the hook-image-puller DaemonSet)
# "{{ $new_checksum }}" != "{{ $old_checksum}}"
            {{- end }}
        {{- else -}}
# prePuller.hook.enabled={{ .Values.apps.jupyterhub.prePuller.hook.enabled }}
# prePuller.hook.pullOnlyOnChanges={{ .Values.apps.jupyterhub.prePuller.hook.pullOnlyOnChanges }}
        {{- end }}
    {{- end }}
{{- end }}
