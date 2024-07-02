import shutil


from ch_cli_tools.utils import *


HERE = os.path.dirname(os.path.realpath(__file__)).replace(os.path.sep, '/')


def test_image_name_from_docker_path():
    assert image_name_from_dockerfile_path("a") == 'a'
    assert image_name_from_dockerfile_path("a/b") == 'a-b'
    assert image_name_from_dockerfile_path("a/src/b") == 'a-b'
    assert image_name_from_dockerfile_path("a/tasks/b") == 'a-b'
    assert image_name_from_dockerfile_path("cloudharness/a/b") == 'cloudharness-a-b'
    assert image_name_from_dockerfile_path("cloudharness/a/b", 'reg') == 'reg/cloudharness-a-b'


def test_merge_configuration_directories():
    try:
        basedir = os.path.join(HERE, "resources")
        res_path = os.path.join(basedir, 'conf-res')
        if os.path.exists(res_path):
            shutil.rmtree(res_path)

        merge_configuration_directories(os.path.join(basedir, 'conf-source1'), res_path)
        merge_configuration_directories(os.path.join(basedir, 'conf-source2'), res_path)

        assert os.path.exists(os.path.join(res_path, "a.yaml"))
        assert os.path.exists(os.path.join(res_path, "b.yaml"))
        assert os.path.exists(os.path.join(res_path, "c.yaml"))

        assert os.path.exists(os.path.join(res_path, "sub", "a.yaml"))
        assert os.path.exists(os.path.join(res_path, "sub", "b.yaml"))
        assert os.path.exists(os.path.join(res_path, "sub", "c.yaml"))

        with open(os.path.join(res_path, "a.yaml")) as f:
            a = yaml.load(f)
        assert a['a'] == 'a1'
        assert a['b']['ba'] == 'ba1'
        assert a['b']['bb'] == 'bb'
        assert a['b']['bc'] == 'bc'

        with open(os.path.join(res_path, "sub", "a.yaml")) as f:
            a = yaml.load(f)
        assert a['a'] == 'a1'
        assert a['b']['ba'] == 'ba1'
        assert a['b']['bb'] == 'bb'
        assert a['b']['bc'] == 'bc'
    finally:
        if os.path.exists(res_path):
            shutil.rmtree(res_path)


def test_guess_build_dependencies_from_dockerfile():
    deps = guess_build_dependencies_from_dockerfile(os.path.join(HERE, "resources/applications/myapp"))
    assert len(deps) == 1
    assert deps[0] == "cloudharness-flask"

    deps = guess_build_dependencies_from_dockerfile(os.path.join(HERE, "resources/applications/myapp/tasks/mytask"))
    assert len(deps) == 0


def test_check_docker_manifest_exists():
    assert check_docker_manifest_exists("gcr.io/metacellllc", "cloudharness/cloudharness-base", "latest")
    assert not check_docker_manifest_exists("gcr.io/metacellllc", "cloudharness/cloudharness-base", "RANDOM_TAG")

def test_find_dockerfile_paths():
    
    myapp_path = os.path.join(HERE, "resources/applications/myapp")
    if not os.path.exists(os.path.join(myapp_path, "dependencies/a/.git")):
        os.makedirs(os.path.join(myapp_path, "dependencies/a/.git"))
        
    dockerfiles = find_dockerfiles_paths(myapp_path)
    assert len(dockerfiles) == 2
    assert next(d for d in dockerfiles if d.endswith("myapp")), "Must find the Dockerfile in the root directory"
    assert next(d for d in dockerfiles if d.endswith("myapp/tasks/mytask")), "Must find the Dockerfile in the tasks directory"

def test_docker_image_tag():
    image_names = [
        'nginx',
        'library/nginx',
        'myregistry.local:5000/repo/image',
        'myrepo/myimage:latest',
        'myrepo/myimage:1.0.0-alpha'
    ]

    for image in image_names:
        docker_img = DockerImageTag.from_str(image)
        docker_img_str = str(docker_img)
        assert image == docker_img_str, f'expected {image}, got {docker_img_str}'

    invalid_image_names = [
        #'-invalid/repo',
        #'invalid-/repo',
        'invalid..repo',
        'repo/invalid-.tag',
        'repo/.invalid',
        'repo/invalid_.tag',
        'repo/invalid#repo',
        'repo/invalid@repo',
        'repo/invalid!repo',
        'repo/invalid repo',
        #'repo/this-is-a-repo-with-a-tag-that-is-way-too-long:and-this-tag-is-also-way-too-long-because-it-has-more-than-128-characters-which-is-not-allowed-by-docker',
        '_invalid.hostname/repo',
        #'invalid_hostname/repo',
        'repo/',
        '/repo',
        'myregistry.local:port/repo'
    ]

    for image in invalid_image_names:
        exception_raised = False
        try:
            DockerImageTag.from_str(image)
        except Exception:
            exception_raised = True
        
        assert exception_raised, f"expected exception to be raised for '{image}'"