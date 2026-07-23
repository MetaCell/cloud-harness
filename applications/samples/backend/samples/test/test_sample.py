def test_sample():
    assert True


def test_write_file():
    import socket

    from samples.controllers import test_controller

    # outside a deployment the controller falls back to writing under /tmp/myvolume
    result = test_controller.write_file({"content": "hello"})

    assert result["hostname"] == socket.gethostname()
    assert result["hostname"] in result["filename"]
    with open(result["path"]) as f:
        assert f.read() == "hello"

    result = test_controller.write_file()
    with open(result["path"]) as f:
        assert socket.gethostname() in f.read()
