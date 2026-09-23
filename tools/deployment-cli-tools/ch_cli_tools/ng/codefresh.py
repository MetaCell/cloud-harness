from functools import lru_cache

from .model import CHValues, register_file


@register_file(
    "codefresh_template",
    lambda root: root / "deployment-configuration" / "codefresh-template.yaml",
)
class CHCodefreshTemplate(CHValues):
    def __init__(self, path, parent, env=None):
        super().__init__(path, parent, env or "project")
        self.default = CHValues(
            self.project.ch_path
            / "deployment-configuration"
            / "codefresh-template.yaml",
            self.project,
        )

    @lru_cache
    def all_values(self):
        return self.default.merge_with(self)


@register_file(
    "codefresh", lambda root: root / "deployment" / "codefresh.yaml", only_env=True
)
class CHCodefresh(CHValues):
    def generate(self): ...
