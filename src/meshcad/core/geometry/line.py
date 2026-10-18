"""Segmento de recta."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from meshcad.core.geometry.entity import GeometryEntity
from meshcad.core.geometry.point import Point2D


@dataclass(frozen=True)
class Line(GeometryEntity):
    start: Point2D
    end: Point2D

    def start_point(self) -> Point2D:
        return self.start

    def end_point(self) -> Point2D:
        return self.end

    def length(self) -> float:
        return self.start.distance_to(self.end)

    def evaluate(self, t: float) -> Point2D:
        t = max(0.0, min(1.0, t))
        return Point2D(
            self.start.x + (self.end.x - self.start.x) * t,
            self.start.y + (self.end.y - self.start.y) * t,
        )

    def sample(self, n: int) -> List[Point2D]:
        if n < 2:
            raise ValueError("n debe ser >= 2")
        return [self.evaluate(i / (n - 1)) for i in range(n)]

    def bounding_box(self) -> Tuple[Point2D, Point2D]:
        return (
            Point2D(min(self.start.x, self.end.x), min(self.start.y, self.end.y)),
            Point2D(max(self.start.x, self.end.x), max(self.start.y, self.end.y)),
        )

    def get_grips(self) -> List[Point2D]:
        return []
