"""Topological vertex: point with a stable identifier."""

from __future__ import annotations

from dataclasses import dataclass

from meshcad.core.geometry.point import Point2D


@dataclass(frozen=True)
class Vertex:
    """Vertice topologico.

    El id es asignado por el contenedor Topology. El punto es la
    representacion geometrica del vertex.
    """

    id: int
    point: Point2D

    def __repr__(self) -> str:
        return "Vertex(id={}, point={!r})".format(self.id, self.point)
