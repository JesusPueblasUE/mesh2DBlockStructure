"""Distribuciones de nodos a lo largo de una entidad geometrica."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from meshcad.core.geometry.entity import GeometryEntity
from meshcad.core.geometry.point import Point2D


class NodeDistribution(ABC):
    """Interfaz de las distribuciones de nodos.

    Una distribucion produce una lista de parametros t en [0, 1],
    estrictamente creciente, con el primero igual a 0 y el ultimo a 1.
    La conversion a puntos la hace la entidad geometrica via evaluate().
    """

    @abstractmethod
    def positions(self, n: int) -> List[float]:
        """Devuelve n parametros en [0, 1] con extremos fijos."""

    def sample(self, geometry: GeometryEntity, n: int) -> List[Point2D]:
        return [geometry.evaluate(t) for t in self.positions(n)]

    def __repr__(self) -> str:  # pragma: no cover
        return self.__class__.__name__ + "()"


class UniformDistribution(NodeDistribution):
    """Distribucion equiespaciada en el parametro t."""

    def positions(self, n: int) -> List[float]:
        if n < 2:
            raise ValueError("n debe ser >= 2")
        return [i / (n - 1) for i in range(n)]
