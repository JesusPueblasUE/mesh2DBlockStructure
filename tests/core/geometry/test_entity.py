import pytest

from meshcad.core.geometry.entity import GeometryEntity
from meshcad.core.geometry.point import Point2D


def test_cannot_instantiate_abstract():
    with pytest.raises(TypeError):
        GeometryEntity()  # type: ignore[abstract]


def test_subclass_must_implement_all_methods():
    class Incomplete(GeometryEntity):
        def start_point(self):
            return Point2D(0, 0)

    with pytest.raises(TypeError):
        Incomplete()  # type: ignore[abstract]


def test_complete_subclass_can_be_instantiated():
    class Dummy(GeometryEntity):
        def start_point(self):
            return Point2D(0, 0)

        def end_point(self):
            return Point2D(1, 0)

        def length(self):
            return 1.0

        def evaluate(self, t):
            return Point2D(t, 0.0)

        def sample(self, n):
            return [Point2D(0, 0), Point2D(1, 0)]

        def bounding_box(self):
            return (Point2D(0, 0), Point2D(1, 0))
            
        def get_grips(self):
            return []

    d = Dummy()
    assert d.length() == 1.0
    assert d.start_point() == Point2D(0, 0)
