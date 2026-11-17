"""Task commands derived from the Dockerfiles, from parsing to the Argo task that uses them.

Argo's emissary executor reads an image's ENTRYPOINT/CMD from the registry when a container has
no command, which needs registry credentials. The commands are derived from the task Dockerfiles
at generation time and carried in the generated values instead.
"""

from cloudharness_model import HarnessMainConfig


# Schema


def _main_config(**extra):
    return HarnessMainConfig.from_dict(
        {
            "local": False,
            "secured_gatekeepers": False,
            "domain": "my.local",
            "namespace": "test",
            "mainapp": "myapp",
            "apps": {},
            **extra,
        }
    )


def test_main_config_model_carries_task_commands():
    config = _main_config(**{"task-commands": {"t": ["a", "b"]}})

    assert config.task_commands == {"t": ["a", "b"]}
    assert config.to_dict()["task-commands"] == {"t": ["a", "b"]}


def test_main_config_model_does_not_require_task_commands():
    config = _main_config()

    assert config.task_commands is None
