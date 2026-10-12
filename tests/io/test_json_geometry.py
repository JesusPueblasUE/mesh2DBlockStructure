import math

import pytest

from meshcad.core.geometry.arc import Arc
from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.geometry.spline import Spline
from meshcad.core.mesh.distribution import (
    BiasedDistribution,
    UniformDistribution,
)
from meshcad.io.json_io import (
    distribution_from_dict,
    distribution_to_dict,
    geometry_from_dict,
    geometry_to_dict,
)


def test_line_round_trip():
    line = Line(Point2D(1.0, 2.0), Point2D(3.5, -4.0))
    data = geometry_to_dict(line)
    assert data["type"] == "line"
    back = geometry_from_dict(data)
    assert back == line


def test_arc_round_trip():
    arc = Arc(Point2D(0, 0), 2.5, 0.1, math.pi / 3)
    data = geometry_to_dict(arc)
    assert data["type"] == "arc"
    back = geometry_from_dict(data)
    assert math.isclose(back.radius, arc.radius)
    assert math.isclose(back.start_angle, arc.start_angle)
    assert math.isclose(back.end_angle, arc.end_angle)
    assert back.center == arc.center


def test_spline_round_trip():
    pts = (Point2D(0, 0), Point2D(1, 2), Point2D(2.5, -1), Point2D(4, 0))
    sp = Spline(pts)
    data = geometry_to_dict(sp)
    assert data["type"] == "spline"
    back = geometry_from_dict(data)
    assert back.points == pts


def test_geometry_type_discriminator_required():
    with pytest.raises(ValueError):
        geometry_from_dict({"foo": "bar"})


def test_uniform_round_trip():
    d = UniformDistribution()
    data = distribution_to_dict(d)
    assert data == {"type": "uniform"}
    back = distribution_from_dict(data)
    assert isinstance(back, UniformDistribution)


def test_biased_round_trip():
    d = BiasedDistribution(bias=1.7, from_start=False)
    data = distribution_to_dict(d)
    back = distribution_from_dict(data)
    assert isinstance(back, BiasedDistribution)
    assert math.isclose(back.bias, 1.7)
    assert back.from_start is False


def test_unknown_distribution_raises():
    with pytest.raises(ValueError):
        distribution_from_dict({"type": "unknown"})
