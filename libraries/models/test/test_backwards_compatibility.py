
from cloudharness_model import  User



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
