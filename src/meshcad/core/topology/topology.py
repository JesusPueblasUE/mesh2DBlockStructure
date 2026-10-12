"""Contenedor de vertices y aristas con identificadores unicos."""

from __future__ import annotations

from itertools import count
from typing import Dict, List, Optional

from meshcad.core.geometry.entity import GeometryEntity
from meshcad.core.geometry.point import Point2D
from meshcad.core.topology.edge import Edge
from meshcad.core.topology.vertex import Vertex

TOL = 1e-7


class Topology:
    """Almacen de vertices y aristas.

    Los loops no se guardan aqui: solo referencian aristas por id. Asi
    varios loops pueden compartir exactamente la misma arista sin duplicar
    geometria ni distribuciones de nodos.
    """

    def __init__(self) -> None:
        self._vertices: Dict[int, Vertex] = {}
        self._edges: Dict[int, Edge] = {}
        self._vertex_ids = count(0)
        self._edge_ids = count(0)

    # ----------------------------- vertices ----------------------------- #

    def add_vertex(self, point: Point2D) -> Vertex:
        v = Vertex(next(self._vertex_ids), point)
        self._vertices[v.id] = v
        return v

    def get_vertex(self, vertex_id: int) -> Vertex:
        try:
            return self._vertices[vertex_id]
        except KeyError:
            raise KeyError("Vertice {} no existe".format(vertex_id))

    def has_vertex(self, vertex_id: int) -> bool:
        return vertex_id in self._vertices

    def vertices(self) -> List[Vertex]:
        return list(self._vertices.values())

    def find_vertex_at(self, point: Point2D, tol: float = TOL) -> Optional[Vertex]:
        for v in self._vertices.values():
            if v.point.distance_to(point) <= tol:
                return v
        return None

    # ------------------------------ edges ------------------------------- #

    def add_edge(
        self,
        start_vertex: Vertex,
        end_vertex: Vertex,
        geometry: GeometryEntity,
    ) -> Edge:
        if not self.has_vertex(start_vertex.id):
            raise ValueError("start_vertex no pertenece a esta topologia")
        if not self.has_vertex(end_vertex.id):
            raise ValueError("end_vertex no pertenece a esta topologia")
        if geometry.start_point().distance_to(start_vertex.point) > TOL:
            raise ValueError(
                "El punto inicial de la geometria no coincide con start_vertex"
            )
        if geometry.end_point().distance_to(end_vertex.point) > TOL:
            raise ValueError(
                "El punto final de la geometria no coincide con end_vertex"
            )
        e = Edge(next(self._edge_ids), start_vertex.id, end_vertex.id, geometry)
        self._edges[e.id] = e
        return e

    def get_edge(self, edge_id: int) -> Edge:
        try:
            return self._edges[edge_id]
        except KeyError:
            raise KeyError("Arista {} no existe".format(edge_id))

    def has_edge(self, edge_id: int) -> bool:
        return edge_id in self._edges

    def edges(self) -> List[Edge]:
        return list(self._edges.values())

    # ------------------------------- misc ------------------------------- #

    def __len__(self) -> int:
        return len(self._vertices) + len(self._edges)

    def __repr__(self) -> str:
        return "Topology(vertices={}, edges={})".format(
            len(self._vertices), len(self._edges)
        )
