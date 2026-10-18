import math

from meshcad.core.geometry.arc import Arc
from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.geometry.spline import Spline
from meshcad.core.topology.topology import Topology


def test_move_line_vertex():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    e = t.add_edge(v0, v1, Line(v0.point, v1.point))

    t.move_vertex(v1.id, Point2D(2, 3))
    new_e = t.get_edge(e.id)
    assert new_e.geometry.end == Point2D(2, 3)
    assert new_e.geometry.start == Point2D(0, 0)


def test_move_arc_endpoint_reconnects():
    t = Topology()
    v0 = t.add_vertex(Point2D(1, 0))
    v1 = t.add_vertex(Point2D(0, 1))
    arc = Arc(Point2D(0, 0), 1.0, 0.0, math.pi / 2)
    e = t.add_edge(v0, v1, arc)

    # Movemos v0 a (2,0)
    t.move_vertex(v0.id, Point2D(2, 0))
    new_arc = t.get_edge(e.id).geometry
    assert isinstance(new_arc, Arc)
    # El arco se recalcula para pasar exactamente por los dos extremos
    assert math.isclose(new_arc.start_point().distance_to(Point2D(2, 0)), 0.0, abs_tol=1e-7)
    assert math.isclose(new_arc.end_point().distance_to(Point2D(0, 1)), 0.0, abs_tol=1e-7)


def test_move_arc_center_translates():
    t = Topology()
    v0 = t.add_vertex(Point2D(1, 0))
    v1 = t.add_vertex(Point2D(0, 1))
    arc = Arc(Point2D(0, 0), 1.0, 0.0, math.pi / 2)
    e = t.add_edge(v0, v1, arc)

    # Movemos el centro (grip 0) a (1, 1)
    t.move_edge_grip(e.id, 0, Point2D(1, 1))
    new_arc = t.get_edge(e.id).geometry
    assert isinstance(new_arc, Arc)
    assert new_arc.center == Point2D(1, 1)
    # Los extremos tambien se mueven solidariamente
    assert t.get_vertex(v0.id).point == Point2D(2, 1)
    assert t.get_vertex(v1.id).point == Point2D(1, 2)


def test_move_spline_inner_grip():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(2, 0))
    sp = Spline((Point2D(0, 0), Point2D(1, 1), Point2D(2, 0)))
    e = t.add_edge(v0, v1, sp)

    t.move_edge_grip(e.id, 0, Point2D(1, 2))
    new_sp = t.get_edge(e.id).geometry
    assert isinstance(new_sp, Spline)
    assert new_sp.points[1] == Point2D(1, 2)
