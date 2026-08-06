"""Helpers to read the `harness.secrets` definitions.

A secret is defined either in the simple form

    secrets:
      mySecret: "a value"

or in the rich form, which selects a secret manager and carries the settings it needs

    secrets:
      mySecret:
        manager: onepassword
        default: "a value"
        path: vaults/my-vault/items/my-item

See `deployment-configuration/helm/templates/_secrets.tpl` for the Helm side.
"""

from typing import Any, Optional, TypedDict, Union

CLOUDHARNESS_MANAGER = "cloudharness"
UNMANAGED = None


class SecretConfigDict(TypedDict, total=False):
    """The rich form of a secret definition. Manager specific settings (`path` for
    onepassword, `arn` for aws, ...) are added next to these entries."""
    manager: Optional[str]
    default: Optional[str]


# mirrors the SecretsMap schema: a secret is a plain value or a secret configuration
SecretDefinition = Union[str, SecretConfigDict, None]


def _plain(definition: Any) -> Any:
    """The plain form of a secret definition.

    Definitions reach the helpers either as raw values, the way they appear in
    `values.yaml`, or wrapped in the generated `SecretDefinition` union model when they
    come from a parsed `HarnessMainConfig`. Both are reduced to a value or a plain dict.
    """
    definition = getattr(definition, "actual_instance", definition)
    as_dict = getattr(definition, "to_dict", None)
    return as_dict() if as_dict else definition


def is_secret_config(definition: SecretDefinition) -> bool:
    """Whether the secret uses the rich form, which nests the value under `default`."""
    return isinstance(_plain(definition), dict)


def secret_manager(definition: SecretDefinition) -> Optional[str]:
    """Name of the secret manager handling a secret definition.

    Returns `cloudharness` for the simple form and whenever no manager is specified,
    `None` when the manager is explicitly null, meaning the secret is not managed by
    CloudHarness at all.
    """
    definition = _plain(definition)
    if not isinstance(definition, dict):
        return CLOUDHARNESS_MANAGER
    if "manager" not in definition:
        return CLOUDHARNESS_MANAGER
    manager = definition["manager"]
    if manager is None or manager == "":
        return UNMANAGED
    return str(manager)


def is_cloudharness_managed(definition: SecretDefinition) -> bool:
    """Whether the secret value is handled by CloudHarness itself."""
    return secret_manager(definition) == CLOUDHARNESS_MANAGER


def secret_value(definition: SecretDefinition) -> Optional[str]:
    """Value of a secret definition: the definition itself in the simple form, the
    `default` entry in the rich form.

    `None` (configure later) and `""` (generate a static random value) keep their meaning
    in both forms.
    """
    definition = _plain(definition)
    if not isinstance(definition, dict):
        return definition
    return definition.get("default")


def secret_definition_error(definition: Any) -> Optional[str]:
    """Describe why a secret definition is malformed, `None` when it is well formed.

    Only the shape shared by every manager is checked: manager names are not validated
    against a known list, as managers can be contributed by any application's helm
    templates, which are never read here.
    """
    definition = _plain(definition)
    if definition is None or isinstance(definition, (str, int, float, bool)):
        return None
    if not isinstance(definition, dict):
        return f"expected a secret value or a secret configuration, got {type(definition).__name__}"
    manager = definition.get("manager")
    if manager is not None and not isinstance(manager, str):
        return "`manager` must be the name of a secret manager, or null for an unmanaged secret"
    default = definition.get("default")
    if isinstance(default, (dict, list)):
        return "`default` must be a plain secret value"
    return None
