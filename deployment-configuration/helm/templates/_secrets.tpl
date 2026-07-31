{{/* vim: set filetype=mustache: */}}

{{/*
Secret managers framework.

An application secret is defined either in the simple form

  harness:
    secrets:
      mySecret: "a value"

or in the rich form

  harness:
    secrets:
      mySecret:
        manager: onepassword
        default: "a value"
        # ... manager specific fields

The manager is resolved as follows:
  * no `manager` key, or `manager: cloudharness` -> `cloudharness` (the built-in behaviour:
    the value is written to the application secret, random values are generated when needed)
  * `manager:` (explicit null or empty) -> `unmanaged`: CloudHarness renders nothing, the
    secret entry is expected to be created out of band (e.g. `kubectl edit secret <app>`)
  * any other value -> the named secret manager, which is responsible for materializing a
    Kubernetes Secret holding the value.

A secret manager named `X` is implemented by defining two templates:

  * `deploy_utils.secretmanager.X.resource`: renders the Kubernetes resources needed to
    materialize the secret (e.g. a `OnePasswordItem` or an `ExternalSecret`).
  * `deploy_utils.secretmanager.X.ref`: outputs `<kubernetes secret name>/<key>`, telling
    CloudHarness where the value ends up so that it can be mounted with the application secrets.

Both are called with the context
  (dict "root" $ "app" $app "name" <secret name> "spec" <secret definition> "resourceName" <sanitized name>)

Managers can be added by CloudHarness or by any application: templates defined in
`<application>/deploy/templates` are collected into the same chart and therefore share the
same template namespace.
*/}}

{{/*
Resolve the manager of a secret definition.
Outputs `cloudharness`, `unmanaged` or the manager name.
Usage: {{ include "deploy_utils.secretManager" (dict "spec" $secretDefinition) }}
*/}}
{{- define "deploy_utils.secretManager" -}}
{{- $manager := "cloudharness" -}}
{{- if kindIs "map" .spec -}}
  {{- if hasKey .spec "manager" -}}
    {{- $declared := get .spec "manager" -}}
    {{- if kindIs "invalid" $declared -}}
      {{- $manager = "unmanaged" -}}
    {{- else -}}
      {{- if eq (toString $declared) "" -}}
        {{- $manager = "unmanaged" -}}
      {{- else -}}
        {{- $manager = toString $declared -}}
      {{- end -}}
    {{- end -}}
  {{- end -}}
{{- end -}}
{{- $manager -}}
{{- end -}}

{{/*
Tells whether a secret definition is handled by an external secret manager.
Outputs `true` or the empty string.
Usage: {{ if include "deploy_utils.secretIsExternal" (dict "spec" $secretDefinition) }}
*/}}
{{- define "deploy_utils.secretIsExternal" -}}
{{- if not (has (include "deploy_utils.secretManager" (dict "spec" .spec)) (list "cloudharness" "unmanaged")) -}}
true
{{- end -}}
{{- end -}}

{{/*
Resolve the value of a secret definition: the definition itself in the simple form,
the `default` entry in the rich form. Empty when not defined.
Usage: {{ include "deploy_utils.secretValue" (dict "spec" $secretDefinition) }}
*/}}
{{- define "deploy_utils.secretValue" -}}
{{- if kindIs "map" .spec -}}
  {{- if hasKey .spec "default" -}}
    {{- $default := get .spec "default" -}}
    {{- if not (kindIs "invalid" $default) -}}
      {{- $default -}}
    {{- end -}}
  {{- end -}}
{{- else -}}
  {{- if not (kindIs "invalid" .spec) -}}
    {{- .spec -}}
  {{- end -}}
{{- end -}}
{{- end -}}

{{/*
Tells whether an application has secrets handled by CloudHarness itself, i.e. whether
CloudHarness creates the application secret.
Outputs `true` or the empty string.
Usage: {{ if include "deploy_utils.hasManagedSecrets" (dict "app" $app) }}
*/}}
{{- define "deploy_utils.hasManagedSecrets" -}}
{{- $managed := "" -}}
{{- range $name, $spec := .app.harness.secrets -}}
  {{- if eq (include "deploy_utils.secretManager" (dict "spec" $spec)) "cloudharness" -}}
    {{- $managed = "true" -}}
  {{- end -}}
{{- end -}}
{{- $managed -}}
{{- end -}}

{{/*
Name of the Kubernetes resource materializing an externally managed secret.
Usage: {{ include "deploy_utils.secretResourceName" (dict "app" $app "name" $secretName) }}
*/}}
{{- define "deploy_utils.secretResourceName" -}}
{{- printf "%s-%s" .app.harness.deployment.name .name | lower | replace "_" "-" | replace "." "-" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Look up a manager setting, first in the secret definition, then in the manager global
configuration, falling back to the given default.
Usage: {{ include "deploy_utils.secretManagerSetting" (dict "spec" $spec "conf" $conf "key" "store" "default" "") }}
*/}}
{{- define "deploy_utils.secretManagerSetting" -}}
{{- $value := .default -}}
{{- if kindIs "map" .conf -}}
  {{- if hasKey .conf .key -}}
    {{- $declared := index .conf .key -}}
    {{- if not (kindIs "invalid" $declared) -}}
      {{- $value = $declared -}}
    {{- end -}}
  {{- end -}}
{{- end -}}
{{- if kindIs "map" .spec -}}
  {{- if hasKey .spec .key -}}
    {{- $declared := index .spec .key -}}
    {{- if not (kindIs "invalid" $declared) -}}
      {{- $value = $declared -}}
    {{- end -}}
  {{- end -}}
{{- end -}}
{{- $value -}}
{{- end -}}

{{/*
Render the volume exposing the secrets of an application as files.
All secrets, whatever their manager, are exposed in the same directory, so that
`cloudharness.utils.secrets.get_secret` finds them by name.
Usage: {{ include "deploy_utils.secretsVolume" (dict "root" $root "app" $app "name" "secrets" "secretName" $app.harness.deployment.name) }}
*/}}
{{- define "deploy_utils.secretsVolume" -}}
{{- $root := .root -}}
{{- $app := .app -}}
{{- $managed := include "deploy_utils.hasManagedSecrets" (dict "app" $app) -}}
{{- $external := list -}}
{{- range $name, $spec := $app.harness.secrets -}}
  {{- if include "deploy_utils.secretIsExternal" (dict "spec" $spec) -}}
    {{- $manager := include "deploy_utils.secretManager" (dict "spec" $spec) -}}
    {{- $context := dict "root" $root "app" $app "name" $name "spec" $spec "resourceName" (include "deploy_utils.secretResourceName" (dict "app" $app "name" $name)) -}}
    {{- $ref := splitList "/" (include (printf "deploy_utils.secretmanager.%s.ref" $manager) $context) -}}
    {{- $external = append $external (dict "path" $name "secretName" (first $ref) "key" (last $ref)) -}}
  {{- end -}}
{{- end -}}
- name: {{ .name }}
{{- if $external }}
  projected:
    sources:
      - secret:
          name: {{ .secretName }}
          {{- if not $managed }}
          optional: true
          {{- end }}
      {{- range $source := $external }}
      - secret:
          name: {{ $source.secretName }}
          items:
            - key: {{ $source.key }}
              path: {{ $source.path }}
      {{- end }}
{{- else }}
  secret:
    secretName: {{ .secretName }}
    {{- if not $managed }}
    optional: true
    {{- end }}
{{- end }}
{{- end -}}

{{/*
Render the resources materializing the externally managed secrets of an application.
Usage: {{ include "deploy_utils.secretManagerResources" (dict "root" $root "app" $app) }}
*/}}
{{- define "deploy_utils.secretManagerResources" -}}
{{- $root := .root -}}
{{- $app := .app -}}
{{- range $name, $spec := .app.harness.secrets }}
  {{- if include "deploy_utils.secretIsExternal" (dict "spec" $spec) }}
    {{- $manager := include "deploy_utils.secretManager" (dict "spec" $spec) }}
    {{- $context := dict "root" $root "app" $app "name" $name "spec" $spec "resourceName" (include "deploy_utils.secretResourceName" (dict "app" $app "name" $name)) }}
---
{{ include (printf "deploy_utils.secretmanager.%s.resource" $manager) $context }}
  {{- end }}
{{- end }}
{{- end -}}

{{/*
Built-in manager: 1Password, through the 1Password Kubernetes Operator.

  harness:
    secrets:
      mySecret:
        manager: onepassword
        # full item path, or just the item name when `secretmanagers.onepassword.vault` is set
        path: vaults/my-vault/items/my-item
        # item field holding the value, `password` when not set
        field: password

The operator creates one Secret per OnePasswordItem, named after it, with the item fields as keys.
*/}}
{{- define "deploy_utils.secretmanager.onepassword.resource" -}}
{{- $conf := dict -}}
{{- if kindIs "map" .root.Values.secretmanagers -}}
  {{- if kindIs "map" (index .root.Values.secretmanagers "onepassword") -}}
    {{- $conf = index .root.Values.secretmanagers "onepassword" -}}
  {{- end -}}
{{- end -}}
{{- $path := include "deploy_utils.secretManagerSetting" (dict "spec" .spec "conf" dict "key" "path" "default" "") -}}
{{- if not $path -}}
  {{- fail (printf "Secret %s of application %s: the onepassword manager requires a 'path'" .name .app.harness.name) -}}
{{- end -}}
{{- if not (contains "/" $path) -}}
  {{- $vault := include "deploy_utils.secretManagerSetting" (dict "spec" .spec "conf" $conf "key" "vault" "default" "") -}}
  {{- if not $vault -}}
    {{- fail (printf "Secret %s of application %s: the onepassword 'path' must be a full item path, or 'secretmanagers.onepassword.vault' must be set" .name .app.harness.name) -}}
  {{- end -}}
  {{- $path = printf "vaults/%s/items/%s" $vault $path -}}
{{- end -}}
apiVersion: {{ include "deploy_utils.secretManagerSetting" (dict "spec" .spec "conf" $conf "key" "apiVersion" "default" "onepassword.com/v1") }}
kind: OnePasswordItem
metadata:
  name: {{ .resourceName }}
  namespace: {{ .root.Values.namespace }}
  labels:
    app: {{ .app.harness.deployment.name }}
spec:
  itemPath: {{ $path | quote }}
{{- end -}}

{{- define "deploy_utils.secretmanager.onepassword.ref" -}}
{{- printf "%s/%s" .resourceName (include "deploy_utils.secretManagerSetting" (dict "spec" .spec "conf" dict "key" "field" "default" "password")) -}}
{{- end -}}

{{/*
Built-in manager: AWS Secrets Manager, through the External Secrets Operator.

  harness:
    secrets:
      mySecret:
        manager: aws
        arn: arn:aws:secretsmanager:eu-west-1:123456789012:secret:my-secret
        # optional json property of the remote secret
        property: password

The store is normally shared by the whole deployment and set in
`secretmanagers.aws.store` / `secretmanagers.aws.storeKind`.
*/}}
{{- define "deploy_utils.secretmanager.aws.resource" -}}
{{- $conf := dict -}}
{{- if kindIs "map" .root.Values.secretmanagers -}}
  {{- if kindIs "map" (index .root.Values.secretmanagers "aws") -}}
    {{- $conf = index .root.Values.secretmanagers "aws" -}}
  {{- end -}}
{{- end -}}
{{- $arn := include "deploy_utils.secretManagerSetting" (dict "spec" .spec "conf" dict "key" "arn" "default" "") -}}
{{- if not $arn -}}
  {{- fail (printf "Secret %s of application %s: the aws manager requires an 'arn'" .name .app.harness.name) -}}
{{- end -}}
{{- $store := include "deploy_utils.secretManagerSetting" (dict "spec" .spec "conf" $conf "key" "store" "default" "") -}}
{{- if not $store -}}
  {{- fail (printf "Secret %s of application %s: the aws manager requires a 'store', set it in 'secretmanagers.aws.store'" .name .app.harness.name) -}}
{{- end -}}
{{- $property := include "deploy_utils.secretManagerSetting" (dict "spec" .spec "conf" dict "key" "property" "default" "") -}}
apiVersion: {{ include "deploy_utils.secretManagerSetting" (dict "spec" .spec "conf" $conf "key" "apiVersion" "default" "external-secrets.io/v1beta1") }}
kind: ExternalSecret
metadata:
  name: {{ .resourceName }}
  namespace: {{ .root.Values.namespace }}
  labels:
    app: {{ .app.harness.deployment.name }}
spec:
  refreshInterval: {{ include "deploy_utils.secretManagerSetting" (dict "spec" .spec "conf" $conf "key" "refreshInterval" "default" "1h") | quote }}
  secretStoreRef:
    name: {{ $store }}
    kind: {{ include "deploy_utils.secretManagerSetting" (dict "spec" .spec "conf" $conf "key" "storeKind" "default" "ClusterSecretStore") }}
  target:
    name: {{ .resourceName }}
    creationPolicy: Owner
  data:
    - secretKey: value
      remoteRef:
        key: {{ $arn | quote }}
        {{- if $property }}
        property: {{ $property | quote }}
        {{- end }}
{{- end -}}

{{- define "deploy_utils.secretmanager.aws.ref" -}}
{{- printf "%s/value" .resourceName -}}
{{- end -}}
