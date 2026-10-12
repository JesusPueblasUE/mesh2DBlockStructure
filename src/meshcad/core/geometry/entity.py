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
    def sample(self, n: int) -> List[Point2D]:
        """Devuelve n puntos a lo largo de la entidad, incluyendo los extremos.

        n debe ser >= 2.
        """

    @abstractmethod
    def bounding_box(self) -> Tuple[Point2D, Point2D]:
        """Devuelve (min_point, max_point) del rectangulo que la contiene."""
