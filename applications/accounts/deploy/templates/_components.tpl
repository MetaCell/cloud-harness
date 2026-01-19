{{- define "deploy_accounts_utils.user_profile_provider_component" -}}
    "org.keycloak.userprofile.UserProfileProvider": [
        {
            "id": "002b69df-9702-40dd-b73e-3a66d161bf11",
            "providerId": "declarative-user-profile",
            "subComponents": {},
            "config": {
                "kc.user.profile.config": [
                    "{\"attributes\":[{\"name\":\"username\",\"displayName\":\"${username}\",\"validations\":{\"length\":{\"min\":3,\"max\":255},\"username-prohibited-characters\":{},\"up-username-not-idn-homograph\":{}},\"permissions\":{\"view\":[\"admin\",\"user\"],\"edit\":[\"admin\",\"user\"]},\"multivalued\":false},{\"name\":\"email\",\"displayName\":\"${email}\",\"validations\":{\"email\":{},\"length\":{\"max\":255}},\"annotations\":{},\"permissions\":{\"view\":[\"admin\",\"user\"],\"edit\":[\"admin\",\"user\"]},\"multivalued\":false},{\"name\":\"firstName\",\"displayName\":\"${firstName}\",\"validations\":{\"length\":{\"max\":255},\"person-name-prohibited-characters\":{}},\"annotations\":{},\"permissions\":{\"view\":[\"admin\",\"user\"],\"edit\":[\"admin\",\"user\"]},\"multivalued\":false},{\"name\":\"lastName\",\"displayName\":\"${lastName}\",\"validations\":{\"length\":{\"max\":255},\"person-name-prohibited-characters\":{}},\"annotations\":{},\"permissions\":{\"view\":[\"admin\",\"user\"],\"edit\":[\"admin\",\"user\"]},\"multivalued\":false}],\"groups\":[{\"name\":\"user-metadata\",\"displayHeader\":\"User metadata\",\"displayDescription\":\"Attributes, which refer to user metadata\"}],\"unmanagedAttributePolicy\":\"ENABLED\"}"
                ]
            }
        }
    ]
{{- end -}}
{{- define "deploy_accounts_utils.key_provider_component" -}}
    "org.keycloak.keys.KeyProvider": [
        {
            "id": "e632ce46-36ad-421a-b1a5-776383cc1565",
            "name": "rsa-generated",
            "providerId": "rsa-generated",
            "subComponents": {},
            "config": {
                "priority": [
                    "100"
                ]
            }
        },
        {
            "id": "b68bee45-a8f0-46ca-b7d9-0df90189736a",
            "name": "hmac-generated-hs512",
            "providerId": "hmac-generated",
            "subComponents": {},
            "config": {
                "priority": [
                    "100"
                ],
                "algorithm": [
                    "HS512"
                ]
            }
        },
        {
            "id": "55960a57-af77-4f4c-8b6e-925c74bb44db",
            "name": "aes-generated",
            "providerId": "aes-generated",
            "subComponents": {},
            "config": {
                "priority": [
                    "100"
                ]
            }
        },
        {
            "id": "ce068675-5cae-434e-851f-09f653ccc604",
            "name": "rsa-enc-generated",
            "providerId": "rsa-enc-generated",
            "subComponents": {},
            "config": {
                "priority": [
                    "100"
                ],
                "algorithm": [
                    "RSA-OAEP"
                ]
            }
        }
    ]
{{- end -}}
#
{{- define "deploy_accounts_utils.components" -}}
    "components": {
        {{template "deploy_accounts_utils.user_profile_provider_component" }},
        {{template "deploy_accounts_utils.key_provider_component" }}
    },
{{- end -}}