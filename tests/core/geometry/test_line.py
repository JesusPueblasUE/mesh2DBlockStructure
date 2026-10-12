import math

import pytest

from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D


def test_start_end():
    line = Line(Point2D(0, 0), Point2D(1, 1))
    assert line.start_point() == Point2D(0, 0)
    assert line.end_point() == Point2D(1, 1)


def test_length():
    line = Line(Point2D(0, 0), Point2D(3, 4))
    assert math.isclose(line.length(), 5.0)


def test_sample_endpoints():
    line = Line(Point2D(0, 0), Point2D(10, 0))
    pts = line.sample(2)
    assert pts == [Point2D(0, 0), Point2D(10, 0)]


def test_sample_middle():
    line = Line(Point2D(0, 0), Point2D(4, 0))
    pts = line.sample(5)
    assert len(pts) == 5
    assert pts[0] == Point2D(0, 0)
    assert pts[-1] == Point2D(4, 0)
    assert math.isclose(pts[2].x, 2.0)


def test_sample_requires_minimum():
    with pytest.raises(ValueError):
        Line(Point2D(0, 0), Point2D(1, 1)).sample(1)


def test_bounding_box():
    line = Line(Point2D(2, 5), Point2D(-1, 0))
    lo, hi = line.bounding_box()
    assert lo == Point2D(-1, 0)
    assert hi == Point2D(2, 5)
