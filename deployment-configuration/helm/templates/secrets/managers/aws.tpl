{{/* vim: set filetype=mustache: */}}

{{/*
================================================================================
Secret manager: aws
================================================================================

Full setup guide: docs/applications/secrets/managers/aws.md

Reads secrets from AWS Secrets Manager through the External Secrets Operator.

Cluster prerequisites
---------------------
The External Secrets Operator must be installed, see https://external-secrets.io/, along
with a `SecretStore` or `ClusterSecretStore` pointing at AWS Secrets Manager and holding
the credentials or the IRSA service account used to read it. CloudHarness only renders the
`ExternalSecret` resources: the operator is what talks to AWS and materializes the
Kubernetes Secrets.

Usage
-----
  harness:
    secrets:
      mySecret:
        manager: aws
        arn: arn:aws:secretsmanager:eu-west-1:123456789012:secret:my-secret
        property: password

Per secret settings
-------------------
  arn        required. ARN, or plain name, of the secret in AWS Secrets Manager. Becomes
             the operator's `remoteRef.key`.
  version    optional. Pins the secret to a `VersionStage` (e.g. `AWSCURRENT`,
             `AWSPREVIOUS`), or to a `VersionId` when prefixed with `uuid/`. Without it,
             the operator resolves `AWSCURRENT`.
  property   optional. Key to extract when the AWS secret holds a JSON document. Without
             it, the whole remote value is used.
  store      optional here, normally set deployment wide (see below).

Deployment wide settings, under `secretmanagers.aws` in the root values
-----------------------------------------------------------------------
  store           required, the name of the store to read from. A store is shared by the
                  whole deployment, so it belongs here rather than on each secret.
  storeKind       optional, defaults to `ClusterSecretStore`. Use `SecretStore` for a
                  store defined in the release namespace.
  refreshInterval optional, defaults to `1h`. How often the operator re-reads AWS.
  apiVersion      optional, defaults to `external-secrets.io/v1beta1`. Override for a
                  cluster running a different version of the operator's CRD.

  secretmanagers:
    aws:
      store: aws-secrets-manager
      storeKind: ClusterSecretStore
      refreshInterval: 1h

These hold no credentials: the store does, and this section is exposed in the allvalues
config map.

What is rendered
----------------
One `ExternalSecret` per secret, named `<deployment name>-<secret name>` (lowercased, with
`_` and `.` replaced by `-`), targeting a Kubernetes Secret of the same name with the value
under a fixed `value` key. CloudHarness mounts it under the secret's own name, next to the
other secrets of the application.

Other AWS Secrets Manager secrets can be reached the same way by adding a manager with a
different store, which is why the store is a setting rather than being hardcoded.

Errors
------
Rendering fails when `arn` is missing, and when no store is configured.
*/}}

{{- define "deploy_utils.secretmanager.aws.resource" -}}
{{- $conf := dict -}}
{{- if kindIs "map" .root.Values.secretmanagers -}}
  {{- if kindIs "map" (index .root.Values.secretmanagers "aws") -}}
    {{- $conf = index .root.Values.secretmanagers "aws" -}}
  {{- end -}}
{{- end -}}
{{/* the arn identifies one specific secret: never a deployment wide setting */}}
{{- $arn := include "deploy_utils.secretManagerSetting" (dict "spec" .spec "conf" dict "key" "arn" "default" "") -}}
{{- if not $arn -}}
  {{- fail (printf "Secret %s of application %s: the aws manager requires an 'arn'" .name .app.harness.name) -}}
{{- end -}}
{{- $store := include "deploy_utils.secretManagerSetting" (dict "spec" .spec "conf" $conf "key" "store" "default" "") -}}
{{- if not $store -}}
  {{- fail (printf "Secret %s of application %s: the aws manager requires a 'store', set it in 'secretmanagers.aws.store'" .name .app.harness.name) -}}
{{- end -}}
{{- $version := include "deploy_utils.secretManagerSetting" (dict "spec" .spec "conf" dict "key" "version" "default" "") -}}
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
        {{- if $version }}
        version: {{ $version | quote }}
        {{- end }}
        {{- if $property }}
        property: {{ $property | quote }}
        {{- end }}
{{- end -}}

{{/*
The operator writes the value under the fixed `value` key of the target Secret.
*/}}
{{- define "deploy_utils.secretmanager.aws.ref" -}}
{{- printf "%s/value" .resourceName -}}
{{- end -}}
