import pytest

from meshcad.core.geometry.point import Point2D
from meshcad.core.topology.vertex import Vertex


def test_create():
    v = Vertex(0, Point2D(1.0, 2.0))
    assert v.id == 0
    assert v.point == Point2D(1.0, 2.0)


def test_equality_by_value():
    a = Vertex(0, Point2D(1.0, 2.0))
    b = Vertex(0, Point2D(1.0, 2.0))
    c = Vertex(1, Point2D(1.0, 2.0))
    assert a == b
    assert a != c


def test_immutable():
    v = Vertex(0, Point2D(0.0, 0.0))
    with pytest.raises(Exception):
        v.id = 99
