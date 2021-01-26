import os
import sys
import logging
import tempfile

from docker import from_env as DockerClient

from .utils import find_dockerfiles_paths, app_name_from_path, merge_configuration_directories
from .constants import NODE_BUILD_IMAGE, APPS_PATH, STATIC_IMAGES_PATH, BASE_IMAGES_PATH, EXCLUDE_PATHS


class Builder:

    def __init__(self, root_paths, include, tag, namespace, domain, registry='', interactive=False,
                 exclude=tuple()):
        self.included = include or []
        self.tag = tag
        self.root_paths = root_paths
        self.registry = registry
        self.interactive = interactive
        self.exclude = exclude
        self.namespace = namespace
        self.domain = domain

        if include:
            logging.info('Building the following subpaths: %s.', ', '.join(include))

    def set_docker_client(self):
        # connect to docker
        try:
            self.client = DockerClient()
            self.client.ping()
        except:
            raise ConnectionRefusedError(
                '\n\nIs docker running? Run "eval(minikube docker-env)" if you are using minikube...')

    def push(self, image_repository):

        logging.info(f"Pushing image {image_repository}")
        for line in self.client.images.push(image_repository, stream=True, decode=True):
            if not 'progressDetail' in line:
                logging.info(line)
            if 'errorDetail' in line:
                raise Exception("Error occurred while pushing image: " + line['errorDetail']['message'])

            # filter the images to build

    def should_build_image(self, image_path, ignore_include=False) -> bool:
        if any(excluded_path in image_path for excluded_path in (EXCLUDE_PATHS + list(self.exclude))):
            return False
        if not self.included:
            if self.interactive:
                answer = input("Do you want to build " + image_path + "? [Y/n]")
                return answer.upper() != 'N'
            return True

        if ignore_include or any(f"/{inc}/" in image_path or image_path.endswith(f"/{inc}") for inc in self.included):
            return True
        logging.info("Skipping build for image %s", image_path)
        return False

    def run(self):
        self.set_docker_client()
        logging.info('Start building docker images')
        for rpath in self.root_paths:
            logging.info('Building from root directory %s', rpath)
            self.find_and_build_under_path(BASE_IMAGES_PATH, rpath, rpath, ignore_include=True)
            self.find_and_build_under_path(STATIC_IMAGES_PATH, None, rpath, ignore_include=True)
            self.find_and_build_under_path(APPS_PATH, None, rpath)

    def find_and_build_under_path(self, base_path, context_path=None, root_path=None, ignore_include=False):
        abs_base_path = os.path.join(root_path, base_path)
        docker_files = (path for path in find_dockerfiles_paths(abs_base_path) if
                        self.should_build_image(path, ignore_include))

        for dockerfile_path in docker_files:
            dockerfile_rel_path = "" if not context_path else os.path.relpath(dockerfile_path, start=context_path)
            # extract image name
            image_name = app_name_from_path(os.path.relpath(dockerfile_path, start=abs_base_path))

            self.build_image(image_name, dockerfile_rel_path,
                             context_path=context_path if context_path else dockerfile_path)

    def build_under_path(self, dpath):
        """ Uses docker sdk to build a docker images from path information """
        image_name = dpath['name']
        dockerfile_rel_path = dpath['rel_path']
        context_path = dpath['context_path']
        dockerfile_path = dpath['abs_path']

        self.build_image(image_name, dockerfile_rel_path,
                         context_path=context_path if context_path else dockerfile_path)

    def build_image(self, image_name, dockerfile_rel_path, context_path=None):

        registry = "" if not self.registry else self.registry.strip(
            '/') + '/'  # make sure the registry ends with only one single /
        # build image
        image_tag = f'{registry}{image_name}:{self.tag}' if self.tag else image_name

        buildargs = dict(TAG=self.tag, REGISTRY=registry, NAMESPACE=self.namespace, DOMAIN=self.domain)

        # print header
        logging.info(f'\n{80 * "#"}\nBuilding {image_tag} \n{80 * "#"}\n')

        logging.info("Build args: " + ",".join(key + ':' + value for key, value in buildargs.items()))

        image, response = self.client.images.build(path=context_path,
                                                   tag=image_tag,
                                                   buildargs=buildargs,
                                                   dockerfile=os.path.join(dockerfile_rel_path,
                                                                           "Dockerfile") if dockerfile_rel_path else None

                                                   )

        # log stream
        for line in response:
            if 'stream' in line and line['stream'] != '\n':
                logging.info(line['stream'].replace('\n', ' ').replace('\r', ''))
        if self.registry:
            self.push(image_tag)

    def log_merging_operation(self, dpaths: [dict]) -> None:
        logging_message = f"\n\nFound multiple dockerfiles for the next image ({dpaths[0]['name']}):\n\n"
        for dpath in dpaths:
            logging_message += f"{dpath['abs_path']}\n"
        logging_message += "\nWill proceed to merge the two folder and build from the result\n\n"
        logging.info(logging_message)
