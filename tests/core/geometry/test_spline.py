import math

import pytest

from meshcad.core.geometry.point import Point2D
from meshcad.core.geometry.spline import Spline


def test_requires_at_least_two_points():
    with pytest.raises(ValueError):
        Spline((Point2D(0, 0),))


def test_start_end():
    s = Spline((Point2D(0, 0), Point2D(1, 1), Point2D(2, 0)))
    assert s.start_point() == Point2D(0, 0)
    assert s.end_point() == Point2D(2, 0)


def test_interpolates_control_points():
    pts = (Point2D(0, 0), Point2D(1, 2), Point2D(3, 1), Point2D(4, 3))
    s = Spline(pts)
    assert s.evaluate(0.0) == pts[0]
    assert s.evaluate(1.0) == pts[-1]


def test_two_points_is_straight():
    s = Spline((Point2D(0, 0), Point2D(4, 0)))
    mid = s.evaluate(0.5)
    assert math.isclose(mid.x, 2.0)
    assert math.isclose(mid.y, 0.0)


def test_sample_count():
    s = Spline((Point2D(0, 0), Point2D(1, 1), Point2D(2, 0)))
    assert len(s.sample(7)) == 7


def test_sample_requires_minimum():
    with pytest.raises(ValueError):
        Spline((Point2D(0, 0), Point2D(1, 1))).sample(1)


def test_length_is_positive_and_bounded():
    s = Spline((Point2D(0, 0), Point2D(1, 1), Point2D(2, 0)))
    total = s.length()
    assert total > s.start_point().distance_to(s.end_point()) - 1e-9
    assert total < 10.0


def test_bounding_box_contains_all_controls():
    pts = (Point2D(-1, -1), Point2D(0, 3), Point2D(4, 2), Point2D(5, -2))
    lo, hi = Spline(pts).bounding_box()
    for p in pts:
        assert lo.x <= p.x <= hi.x
        assert lo.y <= p.y <= hi.y
