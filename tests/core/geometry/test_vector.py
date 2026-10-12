import math

import pytest

from meshcad.core.geometry.vector import Vector2D


def test_arithmetic():
    a = Vector2D(1, 2)
    b = Vector2D(3, 4)
    assert a + b == Vector2D(4, 6)
    assert b - a == Vector2D(2, 2)
    assert a * 2 == Vector2D(2, 4)
    assert 2 * a == Vector2D(2, 4)
    assert -a == Vector2D(-1, -2)


def test_norm():
    assert math.isclose(Vector2D(3, 4).norm(), 5.0)


def test_normalized():
    v = Vector2D(3, 4).normalized()
    assert math.isclose(v.norm(), 1.0)
    assert math.isclose(v.x, 0.6)
    assert math.isclose(v.y, 0.8)


def test_normalized_zero_raises():
    with pytest.raises(ValueError):
        Vector2D(0, 0).normalized()


def test_dot():
    assert Vector2D(1, 2).dot(Vector2D(3, 4)) == 11


def test_cross():
    assert Vector2D(1, 0).cross(Vector2D(0, 1)) == 1
    assert Vector2D(0, 1).cross(Vector2D(1, 0)) == -1


def test_angle():
    assert math.isclose(Vector2D(1, 0).angle(), 0.0)
    assert math.isclose(Vector2D(0, 1).angle(), math.pi / 2)


def test_rotate_90():
    v = Vector2D(1, 0).rotate(math.pi / 2)
    assert math.isclose(v.x, 0.0, abs_tol=1e-12)
    assert math.isclose(v.y, 1.0, abs_tol=1e-12)
