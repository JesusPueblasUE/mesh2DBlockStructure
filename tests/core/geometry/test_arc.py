import math

import pytest

from meshcad.core.geometry.arc import Arc
from meshcad.core.geometry.point import Point2D


def make_quarter():
    return Arc(Point2D(0, 0), 1.0, 0.0, math.pi / 2)


def test_negative_radius_raises():
    with pytest.raises(ValueError):
        Arc(Point2D(0, 0), -1.0, 0.0, 1.0)


def test_start_end():
    arc = make_quarter()
    s = arc.start_point()
    e = arc.end_point()
    assert math.isclose(s.x, 1.0)
    assert math.isclose(s.y, 0.0, abs_tol=1e-12)
    assert math.isclose(e.x, 0.0, abs_tol=1e-12)
    assert math.isclose(e.y, 1.0)


def test_length_quarter():
    arc = make_quarter()
    assert math.isclose(arc.length(), math.pi / 2)


def test_length_semicircle():
    arc = Arc(Point2D(0, 0), 2.0, 0.0, math.pi)
    assert math.isclose(arc.length(), 2.0 * math.pi)


def test_span_wraps_short():
    # CCW desde pi hasta -pi/2 (= 3pi/2) recorre pi/2
    arc = Arc(Point2D(0, 0), 1.0, math.pi, -math.pi / 2)
    assert math.isclose(arc.angle_span(), math.pi / 2)


def test_span_wraps_long():
    # CCW desde -pi/2 hasta pi recorre 1.5*pi
    arc = Arc(Point2D(0, 0), 1.0, -math.pi / 2, math.pi)
    assert math.isclose(arc.angle_span(), 1.5 * math.pi)


def test_sample_count():
    arc = make_quarter()
    assert len(arc.sample(5)) == 5


def test_sample_requires_minimum():
    with pytest.raises(ValueError):
        make_quarter().sample(1)


def test_bounding_box_quarter():
    arc = make_quarter()
    lo, hi = arc.bounding_box()
    assert math.isclose(lo.x, 0.0, abs_tol=1e-12)
    assert math.isclose(lo.y, 0.0, abs_tol=1e-12)
    assert math.isclose(hi.x, 1.0)
    assert math.isclose(hi.y, 1.0)


def test_bounding_box_semicircle_captures_top():
    arc = Arc(Point2D(0, 0), 1.0, 0.0, math.pi)
    lo, hi = arc.bounding_box()
    assert math.isclose(hi.y, 1.0)
