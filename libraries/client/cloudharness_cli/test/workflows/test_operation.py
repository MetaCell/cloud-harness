# coding: utf-8

"""
    Workflows API

    Workflows API

    The version of the OpenAPI document: 0.1.0
    Contact: cloudharness@metacell.us
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


import unittest

from cloudharness_cli.workflows.models.operation import Operation

class TestOperation(unittest.TestCase):
    """Operation unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_instance(self, include_optional) -> Operation:
        """Test Operation
            include_optional is a boolean, when False only required
            params are included, when True both required and
            optional params are included """
        # uncomment below to create an instance of `Operation`
        """
        model = Operation()
        if include_optional:
            return Operation(
                message = '',
                name = '',
                create_time = '2016-08-29T09:12:33.001Z',
                status = 'Pending',
                workflow = ''
            )
        else:
            return Operation(
        )
        """

    def testOperation(self):
        """Test Operation"""
        # inst_req_only = self.make_instance(include_optional=False)
        # inst_req_and_optional = self.make_instance(include_optional=True)

if __name__ == '__main__':
    unittest.main()
