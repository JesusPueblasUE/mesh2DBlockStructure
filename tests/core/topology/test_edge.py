import pytest

from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.topology.edge import Edge, OrientedEdge


def make_edge():
    return Edge(
        id=0,
        start_vertex_id=0,
        end_vertex_id=1,
        geometry=Line(Point2D(0, 0), Point2D(1, 0)),
    )


def test_create():
    e = make_edge()
    assert e.id == 0
    assert e.start_vertex_id == 0
    assert e.end_vertex_id == 1
    assert isinstance(e.geometry, Line)


def test_frozen():
    e = make_edge()
    with pytest.raises(Exception):
        e.id = 99


def test_oriented_default_forward():
    oe = OrientedEdge(edge_id=5)
    assert oe.edge_id == 5
    assert oe.reversed is False


def test_oriented_reversed():
    oe = OrientedEdge(edge_id=5, reversed=True)
    assert oe.edge_id == 5
    assert oe.reversed is True


def test_oriented_equality():
    assert OrientedEdge(3) == OrientedEdge(3)
    assert OrientedEdge(3) != OrientedEdge(3, reversed=True)
