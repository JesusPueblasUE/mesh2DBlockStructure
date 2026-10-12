"""Smoke test: el paquete se importa y expone una version."""


def test_version():
    import meshcad

    assert isinstance(meshcad.__version__, str)
    assert meshcad.__version__
