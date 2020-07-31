import os
import logging
import tempfile

from docker import from_env as DockerClient

from .utils import collect_under_paths, find_dockerfiles_paths, image_name_from_docker_path, merge_configuration_directories
from .constants import NODE_BUILD_IMAGE, APPS_PATH, STATIC_IMAGES_PATH, BASE_IMAGES_PATH

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
        self.set_docker_client()
        for dpaths in collect_under_paths(self.root_paths, self.should_build_image):
            self.merge_and_build_under_path(dpaths)

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

    def merge_and_build_under_path(self, dpaths):
        """ Merge directories and builds image 
        
        If the same folder is found both in cloud-harness and
        a cloud-harness based project, then the directories are 
        merged together in a temporary directory and the image 
        is built on the resulting merge.
        """
        # no folder merge operation required
        if len(dpaths) == 1:
            self.build_under_path(dpaths[0])
        else:
            self.log_merging_operation(dpaths)
            
            # merge using temporary directory
            with tempfile.TemporaryDirectory() as tmpdirname:
                for dpath in dpaths:
                    merge_configuration_directories(dpath['abs_path'], tmpdirname)
                dpaths[0]['abs_path'] = tmpdirname
                self.build_under_path(dpaths[0])

    def build_under_path(self, dpath):
        """ Uses docker sdk to build a docker images from path information """
        image_name = dpath['name']
        dockerfile_rel_path = dpath['rel_path']
        context_path = dpath['context_path']
        dockerfile_path = dpath['abs_path']

        self.build_image(image_name, dockerfile_rel_path,
                             context_path=context_path if context_path else dockerfile_path)


    def build_image(self, image_name, dockerfile_rel_path, context_path=None):

        registry = "" if not self.registry else self.registry + '/'
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


    def log_merging_operation(self, dpaths:[dict]) -> None:
        logging_message = f"\n\nFound multiple dockerfiles for the next image ({dpaths[0]['name']}):\n\n"
        for dpath in dpaths:
            logging_message += f"{dpath['abs_path']}\n"
        logging_message += "\nWill proceed to merge the two folder and build from the result\n\n"
        logging.info(logging_message)