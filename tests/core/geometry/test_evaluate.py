import math

from meshcad.core.geometry.arc import Arc
from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.geometry.spline import Spline


def test_line_evaluate_endpoints():
    line = Line(Point2D(0, 0), Point2D(10, 0))
    assert line.evaluate(0.0) == Point2D(0, 0)
    assert line.evaluate(1.0) == Point2D(10, 0)


def test_line_evaluate_midpoint():
    line = Line(Point2D(0, 0), Point2D(10, 0))
    mid = line.evaluate(0.5)
    assert math.isclose(mid.x, 5.0)
    assert math.isclose(mid.y, 0.0)


def test_line_sample_uses_evaluate():
    line = Line(Point2D(0, 0), Point2D(4, 0))
    assert line.sample(5) == [
        Point2D(0, 0), Point2D(1, 0), Point2D(2, 0), Point2D(3, 0), Point2D(4, 0)
    ]


def test_arc_evaluate_endpoints():
    arc = Arc(Point2D(0, 0), 1.0, 0.0, math.pi / 2)
    s = arc.evaluate(0.0)
    e = arc.evaluate(1.0)
    assert math.isclose(s.x, 1.0)
    assert math.isclose(s.y, 0.0, abs_tol=1e-12)
    assert math.isclose(e.x, 0.0, abs_tol=1e-12)
    assert math.isclose(e.y, 1.0)


def test_arc_evaluate_midpoint_quarter():
    arc = Arc(Point2D(0, 0), 1.0, 0.0, math.pi / 2)
    mid = arc.evaluate(0.5)
    assert math.isclose(mid.x, math.cos(math.pi / 4))
    assert math.isclose(mid.y, math.sin(math.pi / 4))


def test_spline_evaluate_endpoints():
    s = Spline((Point2D(0, 0), Point2D(1, 2), Point2D(3, 1)))
    assert s.evaluate(0.0) == Point2D(0, 0)
    assert s.evaluate(1.0) == Point2D(3, 1)


def test_spline_sample_uses_evaluate():
    s = Spline((Point2D(0, 0), Point2D(1, 1)))
    pts = s.sample(3)
    assert len(pts) == 3
    assert pts[0] == Point2D(0, 0)
    assert pts[-1] == Point2D(1, 1)
    assert math.isclose(pts[1].x, 0.5)
