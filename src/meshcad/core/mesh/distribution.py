"""Node distributions along a geometric entity."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from meshcad.core.geometry.entity import GeometryEntity
from meshcad.core.geometry.point import Point2D


class NodeDistribution(ABC):
    """Interfaz de las distribuciones de nodes.

    Una distribucion produce a lista de parametros t en [0, 1],
    estrictamente creciente, with el first igual a 0 y el ultimo a 1.
    """

    @abstractmethod
    def positions(self, n: int) -> List[float]:
        """Devuelve n parametros en [0, 1] with extremos fijos."""

    def sample(self, geometry: GeometryEntity, n: int) -> List[Point2D]:
        return [geometry.evaluate(t) for t in self.positions(n)]

    def __repr__(self) -> str:  # pragma: no cover
        return self.__class__.__name__ + "()"


class UniformDistribution(NodeDistribution):
    """Distribucion equiespaciada en el parametro t."""

    def positions(self, n: int) -> List[float]:
        if n < 2:
            raise ValueError("n must be >= 2")
        return [i / (n - 1) for i in range(n)]


@dataclass(frozen=True)
class BiasedDistribution(NodeDistribution):
    """Distribucion with espaciado geometrico.

    Los intervalos entre nodes crecen en progresion geometrica de razon
    'bias'. bias=1.0 equivale a uniform. bias>1 concentra nodes al
    start (from_start=True) o al end (from_start=False).
    """

    bias: float = 2.0
    from_start: bool = True

    def __post_init__(self):
        if self.bias <= 0:
            raise ValueError("bias must ser > 0")

    def positions(self, n: int) -> List[float]:
        if n < 2:
            raise ValueError("n must be >= 2")

        if abs(self.bias - 1.0) < 1e-12:
            return [i / (n - 1) for i in range(n)]

        r = self.bias
        denom = r ** (n - 1) - 1.0
        ts = [(r ** i - 1.0) / denom for i in range(n)]

        if self.from_start:
            return ts
        return [1.0 - t for t in reversed(ts)]

    def __repr__(self) -> str:
        return "BiasedDistribution(bias={:g}, from_start={})".format(
            self.bias, self.from_start
        )
