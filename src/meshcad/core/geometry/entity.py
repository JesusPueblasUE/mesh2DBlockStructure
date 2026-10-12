"""Clase base abstracta para las entidades geometricas 2D."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Tuple

from meshcad.core.geometry.point import Point2D


class GeometryEntity(ABC):
    """Interfaz comun a todas las entidades geometricas 2D."""

    @abstractmethod
    def start_point(self) -> Point2D:
        """Punto inicial de la entidad."""

    @abstractmethod
    def end_point(self) -> Point2D:
        """Punto final de la entidad."""

    @abstractmethod
    def length(self) -> float:
        """Longitud total de la entidad."""

    @abstractmethod
    def evaluate(self, t: float) -> Point2D:
        """Evalua la entidad en el parametro normalizado t en [0, 1].

        t=0 devuelve start_point, t=1 devuelve end_point.
        """

    @abstractmethod
    def sample(self, n: int) -> List[Point2D]:
        """Devuelve n puntos equiespaciados en t, incluyendo los extremos."""

    @abstractmethod
    def bounding_box(self) -> Tuple[Point2D, Point2D]:
        """Devuelve (min_point, max_point) del rectangulo que la contiene."""
