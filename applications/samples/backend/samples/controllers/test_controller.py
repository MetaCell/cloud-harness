from cloudharness.models import User

from samples import util


def error():  # noqa: E501
    """test sentry is working

     # noqa: E501


    :rtype: str
    """
    raise Exception("The error we supposed to find here")


def ping():  # noqa: E501
    """test the application is up

     # noqa: E501


    :rtype: str
    """

    import os
    
    expected_environment_variables = {
        'ENVIRONMENT_TEST_A': 'value',
        'ENVIRONMENT_TEST_B': '123',
    }
    
    for key, expected_value in expected_environment_variables.items():
        try:
            environment_value = os.environ[key]
            if environment_value != expected_value:
                raise Exception(f'Expected environment variable {key} to be {expected_value}, but got {environment_value}')
        except KeyError:
            raise Exception(f'Expected to have an environment variable {key} defined')
            
    import time
    return time.time()

def serialization():
    return User(last_name="Last", first_name="First")