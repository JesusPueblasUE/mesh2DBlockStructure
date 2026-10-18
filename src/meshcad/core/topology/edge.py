"""Topological edge and its oriented use within a loop."""

from __future__ import annotations

from dataclasses import dataclass

from meshcad.core.geometry.entity import GeometryEntity


@dataclass(frozen=True)
class Edge:
    """Arista topologica entre dos vertices.

    La geometry subyacente (Line, Arc, Spline) define la forma de la
    edge y va siempre en el sentido start_vertex -> end_vertex.
    Si un loop la recorre en opposite direction, no se duplica la edge:
    se usa OrientedEdge with reversed=True.
    """

    id: int
    start_vertex_id: int
    end_vertex_id: int
    geometry: GeometryEntity

    def __repr__(self) -> str:
        return "Edge(id={}, v{} -> v{})".format(
            self.id, self.start_vertex_id, self.end_vertex_id
        )


@dataclass(frozen=True)
class OrientedEdge:
    """Usage concreto de a edge inside de un loop.

    reversed=False: el loop recorre la edge en su sentido natural
                    (start_vertex -> end_vertex).
    reversed=True:  el loop la recorre in reverse.
    """

    edge_id: int
    reversed: bool = False
