from .model import CHValues, register_file


@register_file(
    "codefresh", lambda root: root / "deployment" / "codefresh.yaml", only_env=True
)
class CHCodefresh(CHValues):
    def generate(self): ...
