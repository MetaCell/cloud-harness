from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from cloudharness_model.models.base_model_ import Model
from cloudharness_model import util


class CpuMemoryConfig(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, cpu=None, memory=None):  # noqa: E501
        """CpuMemoryConfig - a model defined in OpenAPI

        :param cpu: The cpu of this CpuMemoryConfig.  # noqa: E501
        :type cpu: str
        :param memory: The memory of this CpuMemoryConfig.  # noqa: E501
        :type memory: str
        """
        self.openapi_types = {
            'cpu': str,
            'memory': str
        }

        self.attribute_map = {
            'cpu': 'cpu',
            'memory': 'memory'
        }

        self._cpu = cpu
        self._memory = memory

    @classmethod
    def from_dict(cls, dikt) -> 'CpuMemoryConfig':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The CpuMemoryConfig of this CpuMemoryConfig.  # noqa: E501
        :rtype: CpuMemoryConfig
        """
        return util.deserialize_model(dikt, cls)

    @property
    def cpu(self) -> str:
        """Gets the cpu of this CpuMemoryConfig.

          # noqa: E501

        :return: The cpu of this CpuMemoryConfig.
        :rtype: str
        """
        return self._cpu

    @cpu.setter
    def cpu(self, cpu: str):
        """Sets the cpu of this CpuMemoryConfig.

          # noqa: E501

        :param cpu: The cpu of this CpuMemoryConfig.
        :type cpu: str
        """

        self._cpu = cpu

    @property
    def memory(self) -> str:
        """Gets the memory of this CpuMemoryConfig.

          # noqa: E501

        :return: The memory of this CpuMemoryConfig.
        :rtype: str
        """
        return self._memory

    @memory.setter
    def memory(self, memory: str):
        """Sets the memory of this CpuMemoryConfig.

          # noqa: E501

        :param memory: The memory of this CpuMemoryConfig.
        :type memory: str
        """

        self._memory = memory
