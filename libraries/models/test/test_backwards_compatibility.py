
from cloudharness_model import HarnessMainConfig, ApplicationConfig, User, ApplicationHarnessConfig, CDCEvent
from os.path import join, dirname as dn, realpath
import oyaml as yaml

HERE = dn(realpath(__file__))

def test_dict_behaviour():
    user = User(username="a", attributes={"myattr": 1})
    assert user.username == "a"
    assert user["username"] == "a"

    user.username = "b"

    assert user.username == "b"
    assert user["username"] == "b"


    user["username"] = "c"

    assert user.username == "c"
    assert user["username"] == "c"


    user.firstName = "d"
    assert user.first_name == "d"
    assert user["firstName"] == "d"

    user.first_name = "e"
    assert user.first_name == "e"
    assert user["firstName"] == "e"

    u = user.to_dict()
    assert u["first_name"] == "e"
    assert u["firstName"] == "e"

def test_usages():
    with open(join(HERE, "resources/values.yaml")) as f:
        values = yaml.safe_load(f)
        v = HarnessMainConfig.from_dict(values)
    assert v.apps["accounts"].harness.database
    assert v.apps["accounts"].client.id
    assert v.apps["accounts"]["client"].id
    assert v.apps["accounts"]["client"]["id"]

    assert v.apps["accounts"]["testlist"][0].a == 1
    assert v.apps["accounts"]["testlist"][1].a == 2
    assert v.apps["accounts"].testlist[1].a == 2

    assert getattr(v, "idontexist", 1) == 1

    assert [k for k in v.apps.accounts.client] == ["id", "secret"]
