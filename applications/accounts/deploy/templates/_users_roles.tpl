# Accounts _helper.tpl
{{- define "deploy_accounts_utils.role" }}
    {
      "id": {{ uuidv4 | quote }},
      "name": {{ .role| quote }},
      "composite": false,
      "clientRole": true,
      "containerId": {{ .app.harness.name | quote }},
      "attributes": {}
    }
{{- end}}
#
{{- define "deploy_accounts_utils.user" }}
    {
        "username": {{ .user.username | default .user.email | quote }},
        "email": {{ .user.email | default .user.username | quote }},
        "enabled": true,
        "firstName": {{ .user.firstName | default "Test" | quote }},
        "lastName": {{ .user.lastName | default "User" | quote }},
        "credentials": [
            {
                "type": "password",
                "value": {{ .user.password | default "test" | quote }}
            }
        ],
        "realmRoles": {{ .realmRoles | toJson }},
        "clientRoles": {{ .clientRoles | toJson }}
    }
{{- end}}
#
{{- define "deploy_accounts_utils.users_roles" }}
        {{- /*
        The same user can be declared by several apps (e.g. an app and its instances,
        which inherit the app's accounts.users). Keycloak rejects duplicate usernames
        (case-insensitive) in a realm import, so users are merged by username: the first
        declaration wins for the user fields, realm roles are joined and client roles are
        collected per app client.
        */}}
        {{- $users := dict }}
        {{- $keys := list }}
        {{- range $app := .Values.apps }}
          {{- if hasKey $app.harness "accounts" }}
            {{- range $user := $app.harness.accounts.users }}
              {{- $key := $user.username | default $user.email | lower }}
              {{- if not (hasKey $users $key) }}
                {{- $keys = append $keys $key }}
                {{- $_ := set $users $key (dict "user" $user "realmRoles" (list) "clientRoles" (dict)) }}
              {{- end }}
              {{- $entry := get $users $key }}
              {{- $_ := set $entry "realmRoles" (concat $entry.realmRoles (default (list) $user.realmRoles) | uniq) }}
              {{- $_ := set $entry.clientRoles $app.harness.name (default (list) $user.clientRoles) }}
            {{- end }}
          {{- end }}
        {{- end }}
        "users": [
            {{- range $i, $key := $keys }}{{ if $i }},{{ end }}
              {{- $entry := get $users $key }}
            {{ include "deploy_accounts_utils.user" $entry }}
            {{- end }}
        ],
        "roles": {
            "realm": [
                {
                    "id": "70835ad6-1454-4bc5-86a4-f1597e776b75",
                    "name": {{ .Values.apps.accounts.admin.role | quote }},
                    "composite": false,
                    "clientRole": false,
                    "containerId": {{ .Values.namespace | quote }},
                    "attributes": {}
                },
                {
                    "id": "498353dd-88eb-4a5e-99b8-d912e0f20f23",
                    "name": "uma_authorization",
                    "description": "${role_uma_authorization}",
                    "composite": false,
                    "clientRole": false,
                    "containerId": {{ .Values.namespace | quote }},
                    "attributes": {}
                },
                {
                    "id": "f99970f1-958b-4bb8-8b39-0d7498b0ecc4",
                    "name": "offline_access",
                    "description": "${role_offline-access}",
                    "composite": false,
                    "clientRole": false,
                    "containerId": {{ .Values.namespace | quote }},
                    "attributes": {}
                }
            ],
            "client": {
            {{- $k := 0}}
            {{- range $app := .Values.apps }}

              {{- if (hasKey $app.harness "accounts")  }}
                {{- if $k}},{{end}}
                {{ $app.harness.name | quote }}: [
                {{- range $i, $role := $app.harness.accounts.roles }}
                {{if $i}},{{end}}
                {{- include "deploy_accounts_utils.role" (dict "root" $ "app" $app "role" $role) }}
                {{- end }}
                ]
                {{- $k = add1 $k }}
              {{- end }}
            {{- end }}
            }
        },
{{- end -}}
