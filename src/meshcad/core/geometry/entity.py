"""Clase base abstracta para las entidades geometricas 2D."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Tuple

from meshcad.core.geometry.point import Point2D


class GeometryEntity(ABC):
    """Interfaz comun a todas las entidades geometricas 2D."""

    @abstractmethod
    def start_point(self) -> Point2D:
        pass

    @abstractmethod
    def end_point(self) -> Point2D:
        pass

    @abstractmethod
    def length(self) -> float:
        pass

    @abstractmethod
    def evaluate(self, t: float) -> Point2D:
        pass

    @abstractmethod
    def sample(self, n: int) -> List[Point2D]:
        pass

    @abstractmethod
    def bounding_box(self) -> Tuple[Point2D, Point2D]:
        pass

    @abstractmethod
    def get_grips(self) -> List[Point2D]:
        """Devuelve puntos de control internos (no topologicos).

        Los extremos (start/end) los gestiona la topologia, no la
        geometria. Para un arco, el grip es el centro. Para una
        spline, son los puntos de control interiores.
        """
