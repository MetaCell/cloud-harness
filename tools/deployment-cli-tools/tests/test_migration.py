from ch_cli_tools.utils import *
from ch_cli_tools.migration import perform_migration

HERE = os.path.dirname(os.path.realpath(__file__)).replace(os.path.sep, '/')


def test_migration_accept_all():
    found = search_word_in_folder(os.path.join(HERE, './resources/migration/applications'), "CLOUDHARNESS_BASE_DEBIAN")
    print(found)
    assert len(found) == 2
    try:
        perform_migration(os.path.join(HERE, './resources/migration'), accept_all=True)
        found = search_word_in_folder(os.path.join(HERE, './resources/migration/applications'), "CLOUDHARNESS_BASE_DEBIAN")
        print(found)
        assert len(found) == 0

    finally:
        os.system(f'cp -R {os.path.join(HERE, "resources/migration/backup/migration_app")} {os.path.join(HERE, "resources/migration/applications/")}')
    assert len(search_word_in_folder(os.path.join(HERE, './resources/migration/applications'), "CLOUDHARNESS_BASE_DEBIAN")) == 2
