from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from cloudharness_model.models.base_model_ import Model
from cloudharness_model.models.git_dependency_config import GitDependencyConfig
from cloudharness_model import util

from cloudharness_model.models.git_dependency_config import GitDependencyConfig  # noqa: E501

class ApplicationDependenciesConfig(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, hard=None, soft=None, build=None, git=None):  # noqa: E501
        """ApplicationDependenciesConfig - a model defined in OpenAPI

        :param hard: The hard of this ApplicationDependenciesConfig.  # noqa: E501
        :type hard: List[str]
        :param soft: The soft of this ApplicationDependenciesConfig.  # noqa: E501
        :type soft: List[str]
        :param build: The build of this ApplicationDependenciesConfig.  # noqa: E501
        :type build: List[str]
        :param git: The git of this ApplicationDependenciesConfig.  # noqa: E501
        :type git: List[GitDependencyConfig]
        """
        self.openapi_types = {
            'hard': List[str],
            'soft': List[str],
            'build': List[str],
            'git': List[GitDependencyConfig]
        }

        self.attribute_map = {
            'hard': 'hard',
            'soft': 'soft',
            'build': 'build',
            'git': 'git'
        }

        self._hard = hard
        self._soft = soft
        self._build = build
        self._git = git

    @classmethod
    def from_dict(cls, dikt) -> 'ApplicationDependenciesConfig':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The ApplicationDependenciesConfig of this ApplicationDependenciesConfig.  # noqa: E501
        :rtype: ApplicationDependenciesConfig
        """
        return util.deserialize_model(dikt, cls)

    @property
    def hard(self) -> List[str]:
        """Gets the hard of this ApplicationDependenciesConfig.

        Hard dependencies indicate that the application may not start without these other applications.  # noqa: E501

        :return: The hard of this ApplicationDependenciesConfig.
        :rtype: List[str]
        """
        return self._hard

    @hard.setter
    def hard(self, hard: List[str]):
        """Sets the hard of this ApplicationDependenciesConfig.

        Hard dependencies indicate that the application may not start without these other applications.  # noqa: E501

        :param hard: The hard of this ApplicationDependenciesConfig.
        :type hard: List[str]
        """

        self._hard = hard

    @property
    def soft(self) -> List[str]:
        """Gets the soft of this ApplicationDependenciesConfig.

        Soft dependencies indicate that the application will work partially without these other applications.  # noqa: E501

        :return: The soft of this ApplicationDependenciesConfig.
        :rtype: List[str]
        """
        return self._soft

    @soft.setter
    def soft(self, soft: List[str]):
        """Sets the soft of this ApplicationDependenciesConfig.

        Soft dependencies indicate that the application will work partially without these other applications.  # noqa: E501

        :param soft: The soft of this ApplicationDependenciesConfig.
        :type soft: List[str]
        """

        self._soft = soft

    @property
    def build(self) -> List[str]:
        """Gets the build of this ApplicationDependenciesConfig.

        Hard dependencies indicate that the application Docker image build requires these base/common images  # noqa: E501

        :return: The build of this ApplicationDependenciesConfig.
        :rtype: List[str]
        """
        return self._build

    @build.setter
    def build(self, build: List[str]):
        """Sets the build of this ApplicationDependenciesConfig.

        Hard dependencies indicate that the application Docker image build requires these base/common images  # noqa: E501

        :param build: The build of this ApplicationDependenciesConfig.
        :type build: List[str]
        """

        self._build = build

    @property
    def git(self) -> List[GitDependencyConfig]:
        """Gets the git of this ApplicationDependenciesConfig.

          # noqa: E501

        :return: The git of this ApplicationDependenciesConfig.
        :rtype: List[GitDependencyConfig]
        """
        return self._git

    @git.setter
    def git(self, git: List[GitDependencyConfig]):
        """Sets the git of this ApplicationDependenciesConfig.

          # noqa: E501

        :param git: The git of this ApplicationDependenciesConfig.
        :type git: List[GitDependencyConfig]
        """

        self._git = git
