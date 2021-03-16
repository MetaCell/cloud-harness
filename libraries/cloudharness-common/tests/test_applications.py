from cloudharness.applications import ApplicationConfiguration, get_configuration

conf_1 = {

    'harness': {
        'name': 'app1',
        'service': {
            'auto': False
        },
        'deployment': {
            'auto': True
        },
        'sentry': True
    }
}

conf_2 = {

    'harness': {
        'name': 'app2',
        'service': {
            'auto': False
        },
        'deployment': {
            'auto': False
        },
        'sentry': True
    }
}

conf_2sub = {

    'harness': {
        'name': 'app2sub',
        'service': {
            'auto': True
        },
        'deployment': {
            'auto': False
        },
        'sentry': False
    }
}

conf_2['subapp'] = conf_2sub


def test_application_conf():
    uut = ApplicationConfiguration(conf_1)
    assert not uut.is_auto_service()
    assert uut.is_auto_deployment()
    assert uut.is_sentry_enabled()


def test_get_configuration():
    from cloudharness.utils.config import CloudharnessConfig

    CloudharnessConfig.get_configuration().update({
        'apps': {
            'a': conf_1,
            'b': conf_2
        }
    }
    )
    uut = get_configuration('app1')
    assert uut.name == 'app1'
    assert not uut.is_auto_service()
    assert uut.is_auto_deployment()
    assert uut.is_sentry_enabled()

    uut = get_configuration('app2')
    assert uut.name == 'app2'
    assert not uut.is_auto_service()
    assert not uut.is_auto_deployment()
    assert uut.is_sentry_enabled()

    # uut = get_configuration('app2sub') # FIXME this should work
    uut = uut.subapp

    assert uut.name == 'app2sub'
    assert uut.is_auto_service()
    assert not uut.is_auto_deployment()
    assert not uut.is_sentry_enabled()
