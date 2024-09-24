# coding: utf-8

"""
    Volumes manager API

    CloudHarness Volumes manager API

    The version of the OpenAPI document: 0.1.0
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


import unittest

from cloudharness_cli.volumemanager.models.persistent_volume_claim_create import PersistentVolumeClaimCreate

class TestPersistentVolumeClaimCreate(unittest.TestCase):
    """PersistentVolumeClaimCreate unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_instance(self, include_optional) -> PersistentVolumeClaimCreate:
        """Test PersistentVolumeClaimCreate
            include_optional is a boolean, when False only required
            params are included, when True both required and
            optional params are included """
        # uncomment below to create an instance of `PersistentVolumeClaimCreate`
        """
        model = PersistentVolumeClaimCreate()
        if include_optional:
            return PersistentVolumeClaimCreate(
                name = 'pvc-1',
                size = '2Gi (see also https://github.com/kubernetes/community/blob/master/contributors/design-proposals/scheduling/resources.md#resource-quantities)'
            )
        else:
            return PersistentVolumeClaimCreate(
        )
        """

    def testPersistentVolumeClaimCreate(self):
        """Test PersistentVolumeClaimCreate"""
        # inst_req_only = self.make_instance(include_optional=False)
        # inst_req_and_optional = self.make_instance(include_optional=True)

if __name__ == '__main__':
    unittest.main()
