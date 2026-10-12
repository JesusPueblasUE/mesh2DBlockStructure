import math

import pytest

from meshcad.core.geometry.arc import Arc
from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.mesh.distribution import (
    NodeDistribution,
    UniformDistribution,
)


def test_abstract_cannot_instantiate():
    with pytest.raises(TypeError):
        NodeDistribution()  # type: ignore[abstract]


def test_uniform_positions_endpoints():
    d = UniformDistribution()
    ts = d.positions(5)
    assert math.isclose(ts[0], 0.0)
    assert math.isclose(ts[-1], 1.0)
    assert len(ts) == 5


def test_uniform_positions_equally_spaced():
    d = UniformDistribution()
    ts = d.positions(4)
    assert math.isclose(ts[1], 1.0 / 3.0)
    assert math.isclose(ts[2], 2.0 / 3.0)


def test_uniform_requires_min_two():
    d = UniformDistribution()
    with pytest.raises(ValueError):
        d.positions(1)


def test_uniform_samples_on_line():
    d = UniformDistribution()
    line = Line(Point2D(0, 0), Point2D(10, 0))
    pts = d.sample(line, 3)
    assert pts == [Point2D(0, 0), Point2D(5, 0), Point2D(10, 0)]


def test_uniform_samples_on_arc():
    d = UniformDistribution()
    arc = Arc(Point2D(0, 0), 1.0, 0.0, math.pi / 2)
    pts = d.sample(arc, 3)
    assert math.isclose(pts[1].x, math.cos(math.pi / 4))
    assert math.isclose(pts[1].y, math.sin(math.pi / 4))
