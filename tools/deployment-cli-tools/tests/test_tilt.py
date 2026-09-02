import ast
import os
import re
import shutil

from ch_cli_tools.helm import *
from ch_cli_tools.preprocessing import preprocess_build_overrides
from ch_cli_tools.tilt import create_tilt_configuration

HERE = os.path.dirname(os.path.realpath(__file__))
RESOURCES = os.path.join(HERE, 'resources')

CLOUDHARNESS_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))


def test_tilt_imgarg_retrieval(tmp_path):
    """source_images entries (global base-image overrides) must be injected as build
    arguments for every docker_build call in the generated Tiltfile, matching skaffold."""
    out_folder = tmp_path / "test_tilt_imgarg_retrieval"

    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=out_folder,
        include=["samples", "myapp"],
        domain="my.local",
        namespace="test",
        env="nreg",
        local=False,
        tag=1,
        registry="reg",
    )

    source_images = values.get("source_images")
    assert source_images["KEYCLOAK"] == "myregistry.myapp:15.3"
    assert source_images["NODE"] == "node:22-alpine"

    # CLOUDHARNESS_FLASK is also a build dependency of samples and myapp: a source_images
    # override for it must win over the dependency-derived build arg, not be shadowed by it.
    values["source_images"] = dict(source_images) | {"CLOUDHARNESS_FLASK": "myoverride/cloudharness-flask:9.9"}

    BUILD_DIR = "/tmp/build_tilt_imgarg"
    root_paths = preprocess_build_overrides(
        root_paths=[CLOUDHARNESS_ROOT, RESOURCES],
        helm_values=values,
        merge_build_path=BUILD_DIR,
    )

    create_tilt_configuration(
        root_paths=root_paths, helm_values=values, output_path=str(out_folder)
    )

    tiltfile_content = (out_folder / "Tiltfile").read_text()

    def get_buildargs(name) -> dict:
        pattern = re.compile(
            r"docker_build\(ref='[^']*', context='([^']*)', dockerfile='[^']*', build_args=(\{[^}]*\})"
        )
        for context, args_repr in pattern.findall(tiltfile_content):
            if f"applications/{name}" in context:
                return ast.literal_eval(args_repr)
        return {}

    samples_buildargs = get_buildargs("samples")
    assert samples_buildargs["KEYCLOAK"] == "myregistry.myapp:15.3"
    assert samples_buildargs["NODE"] == "node:22-alpine"
    assert samples_buildargs["CLOUDHARNESS_FLASK"] == "myoverride/cloudharness-flask:9.9"

    myapp_buildargs = get_buildargs("myapp")
    assert myapp_buildargs["KEYCLOAK"] == "myregistry.myapp:15.3"
    assert myapp_buildargs["NODE"] == "node:22-alpine"
    assert myapp_buildargs["CLOUDHARNESS_FLASK"] == "myoverride/cloudharness-flask:9.9"

    shutil.rmtree(out_folder)
    shutil.rmtree(BUILD_DIR)
