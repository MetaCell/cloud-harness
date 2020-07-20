import os
import logging

from docker import from_env as DockerClient

from .constants import NODE_BUILD_IMAGE, APPS_PATH, STATIC_IMAGES_PATH, BASE_IMAGES_PATH
from .utils import find_dockerfiles_paths, image_name_from_docker_path


class Builder:

    def __init__(self, root_paths, include, tag, registry='', interactive=False, exclude=tuple()):
        self.included = include or []
        self.tag = tag
        self.root_paths = root_paths
        self.registry = registry
        self.interactive = interactive
        self.exclude = exclude

        if include:
            logging.info('Building the following subpaths: %s.', ', '.join(include))

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

    def should_build_image(self, image_path) -> bool:
        if image_path in self.exclude:
            return False
        if not self.included:
            if self.interactive:
                answer = input("Do you want to build " + image_path + "? [Y/n]")
                return answer.upper() != 'N'
            return True

        if any(inc in image_path for inc in self.included):
            return True
        logging.info("Skipping build for image %s", image_path)
        return False

    def run(self):
        for root_path in self.root_paths:
            self.find_and_build_under_path(BASE_IMAGES_PATH, context_path=root_path, root_path=root_path)
            # Build static images that will be use as base for other images
            self.find_and_build_under_path(STATIC_IMAGES_PATH, root_path=root_path)

            self.find_and_build_under_path(APPS_PATH, root_path=root_path)

    def find_and_build_under_path(self, base_path, context_path=None, root_path=None):
        abs_base_path = os.path.join(root_path, base_path)
        docker_files = (path for path in find_dockerfiles_paths(abs_base_path) if
                        self.should_build_image(path))

        for dockerfile_path in docker_files:
            dockerfile_rel_path = "" if not context_path else os.path.relpath(dockerfile_path, start=context_path)
            # extract image name
            image_name = image_name_from_docker_path(os.path.relpath(dockerfile_path, start=abs_base_path))
            self.build_image(image_name, dockerfile_rel_path,
                             context_path=context_path if context_path else dockerfile_path)

    def build_image(self, image_name, dockerfile_rel_path, context_path=None):

        registry = "" if not self.registry else self.registry + '/'
        # build image
        image_tag = f'{registry}{image_name}:{self.tag}' if self.tag else image_name

        buildargs = dict(TAG=self.tag, REGISTRY=registry)

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
