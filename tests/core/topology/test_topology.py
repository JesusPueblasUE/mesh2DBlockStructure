import pytest

from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.topology.topology import Topology


def test_add_vertex_unique_ids():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    assert v0.id == 0
    assert v1.id == 1
    assert v0.id != v1.id


def test_get_vertex():
    t = Topology()
    v = t.add_vertex(Point2D(2, 3))
    assert t.get_vertex(v.id) is v
    assert t.has_vertex(v.id)
    assert not t.has_vertex(999)


def test_get_vertex_missing_raises():
    t = Topology()
    with pytest.raises(KeyError):
        t.get_vertex(42)


def test_find_vertex_at():
    t = Topology()
    v = t.add_vertex(Point2D(1.0, 1.0))
    assert t.find_vertex_at(Point2D(1.0, 1.0)) is v
    assert t.find_vertex_at(Point2D(1.0 + 1e-10, 1.0)) is v
    assert t.find_vertex_at(Point2D(1.5, 1.5)) is None


def test_add_edge_valid():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    e = t.add_edge(v0, v1, Line(v0.point, v1.point))
    assert e.id == 0
    assert e.start_vertex_id == v0.id
    assert e.end_vertex_id == v1.id


def test_add_edge_geometry_must_match_start():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    with pytest.raises(ValueError):
        t.add_edge(v0, v1, Line(Point2D(5, 5), v1.point))


def test_add_edge_geometry_must_match_end():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    with pytest.raises(ValueError):
        t.add_edge(v0, v1, Line(v0.point, Point2D(9, 9)))


def test_add_edge_foreign_vertex_rejected():
    t1 = Topology()
    t2 = Topology()
    v0 = t2.add_vertex(Point2D(0, 0))
    v1 = t2.add_vertex(Point2D(1, 0))
    with pytest.raises(ValueError):
        t1.add_edge(v0, v1, Line(v0.point, v1.point))


def test_edges_unique_ids():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    e0 = t.add_edge(v0, v1, Line(v0.point, v1.point))
    e1 = t.add_edge(v1, v0, Line(v1.point, v0.point))
    assert e0.id != e1.id


def test_len_and_listing():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    t.add_edge(v0, v1, Line(v0.point, v1.point))
    assert len(t) == 3
    assert len(t.vertices()) == 2
    assert len(t.edges()) == 1
