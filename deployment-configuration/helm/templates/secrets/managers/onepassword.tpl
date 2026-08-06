{{/* vim: set filetype=mustache: */}}

{{/*
================================================================================
Secret manager: onepassword
================================================================================

Full setup guide: docs/applications/secrets/managers/onepassword.md

Reads secrets from 1Password through the 1Password Kubernetes Operator.

Cluster prerequisites
---------------------
The 1Password Kubernetes Operator must be installed in the cluster and connected to a
1Password Connect server, see https://developer.1password.com/docs/k8s/k8s-operator/.
CloudHarness only renders the `OnePasswordItem` custom resources: the operator is what
reaches 1Password and materializes the Kubernetes Secrets.

Usage
-----
  harness:
    secrets:
      mySecret:
        manager: onepassword
        path: vaults/my-vault/items/my-item
        field: password

Per secret settings
-------------------
  path       required. Path of the 1Password item, `vaults/<vault>/items/<item>`. The
             vault part may be omitted, and the item name given alone, when a default
             vault is configured globally (see below).
  field      optional, defaults to `password`. Field of the 1Password item holding the
             value. The operator names the Secret keys after the item fields, so this
             selects which one is exposed to the application.
  apiVersion optional, defaults to `onepassword.com/v1`. Override for a cluster running
             a different version of the operator's CRD.

Deployment wide settings, under `secretmanagers.onepassword` in the root values
-------------------------------------------------------------------------------
  vault      default vault, so that secrets only need to name their item.
  apiVersion as above, applied to every onepassword secret.

  secretmanagers:
    onepassword:
      vault: my-vault

These hold no credentials: the operator authenticates on its own, and this section is
exposed in the allvalues config map.

What is rendered
----------------
One `OnePasswordItem` per secret, named `<deployment name>-<secret name>` (lowercased,
with `_` and `.` replaced by `-`). The operator creates a Kubernetes Secret with the same
name, holding every field of the 1Password item. CloudHarness then mounts only `field`
from it, under the secret's own name, next to the other secrets of the application.

Errors
------
Rendering fails when `path` is missing, and when `path` is an item name alone while no
default vault is configured.
*/}}

{{- define "deploy_utils.secretmanager.onepassword.resource" -}}
{{- $conf := dict -}}
{{- if kindIs "map" .root.Values.secretmanagers -}}
  {{- if kindIs "map" (index .root.Values.secretmanagers "onepassword") -}}
    {{- $conf = index .root.Values.secretmanagers "onepassword" -}}
  {{- end -}}
{{- end -}}
{{/* the item path is never a deployment wide setting: pass an empty conf */}}
{{- $path := include "deploy_utils.secretManagerSetting" (dict "spec" .spec "conf" dict "key" "path" "default" "") -}}
{{- if not $path -}}
  {{- fail (printf "Secret %s of application %s: the onepassword manager requires a 'path'" .name .app.harness.name) -}}
{{- end -}}
{{- if not (contains "/" $path) -}}
  {{/* an item name alone is completed with the globally configured vault */}}
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

{{/*
The operator names the Secret after the OnePasswordItem, and its keys after the item fields.
*/}}
{{- define "deploy_utils.secretmanager.onepassword.ref" -}}
{{- printf "%s/%s" .resourceName (include "deploy_utils.secretManagerSetting" (dict "spec" .spec "conf" dict "key" "field" "default" "password")) -}}
{{- end -}}
