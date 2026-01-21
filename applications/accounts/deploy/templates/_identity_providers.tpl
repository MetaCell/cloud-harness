#
{{- define "deploy_accounts_utils.github_identity_provider" -}}
    {
        "alias": "github",
        "internalId": "a3b32961-038c-41df-8e7c-815cda420aac",
        "providerId": "github",
        "enabled": true,
        "updateProfileFirstLoginMode": "on",
        "trustEmail": false,
        "storeToken": false,
        "addReadTokenRoleOnCreate": false,
        "authenticateByDefault": false,
        "linkOnly": false,
        "firstBrokerLoginFlowAlias": "first broker login",
        "config": {
            "syncMode": "IMPORT",
            "clientSecret": {{ .app.harness.secrets.github_clientSecret | default "<github_clientSecret>" | quote }},
            "clientId": {{ .app.harness.secrets.github_clientId | default "<github_clientId>" | quote }},
            "useJwksUrl": "true"
            }
    }
{{- end -}}
#
{{- define "deploy_accounts_utils.google_identity_provider" -}}
    {
        "alias": "google",
        "internalId": "7f65669a-e52f-426b-a9f6-f37253b00dae",
        "providerId": "google",
        "enabled": true,
        "updateProfileFirstLoginMode": "on",
        "trustEmail": false,
        "storeToken": false,
        "addReadTokenRoleOnCreate": false,
        "authenticateByDefault": false,
        "linkOnly": false,
        "firstBrokerLoginFlowAlias": "first broker login",
        "config": {
            "syncMode": "IMPORT",
            "clientSecret": {{ .app.harness.secrets.google_clientSecret | default "<google_clientSecret>" | quote }},
            "clientId": {{ .app.harness.secrets.google_clientId | default "<google_clientId>" | quote }},
            "useJwksUrl": "true"
        }
    }
{{- end -}}
#
{{- define "deploy_accounts_utils.identity_providers" -}}
    {{- if hasKey .app "identityProviders" -}}
        "identityProviders": [
        {{- range $i, $provider := .app.identityProviders }}
            {{- if $i}},{{end}}
            {{ include (printf "deploy_accounts_utils.%s_identity_provider" $provider) (dict "app" $.app) | indent 12 }}
        {{- end -}}
        ],
    {{- end }}
{{- end -}}