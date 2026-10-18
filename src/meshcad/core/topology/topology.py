"""Contenedor de vertices y aristas con identificadores unicos."""

from __future__ import annotations

import math
from itertools import count
from typing import Dict, List, Optional

from meshcad.core.geometry.arc import Arc
from meshcad.core.geometry.entity import GeometryEntity
from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.geometry.spline import Spline
from meshcad.core.geometry.vector import Vector2D
from meshcad.core.topology.edge import Edge
from meshcad.core.topology.vertex import Vertex

TOL = 1e-7


class Topology:
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
        return self._vertices[vertex_id]

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

    def add_edge(self, start_vertex: Vertex, end_vertex: Vertex,
                 geometry: GeometryEntity) -> Edge:
        if not self.has_vertex(start_vertex.id) or not self.has_vertex(end_vertex.id):
            raise ValueError("vertices extranjeros")
        e = Edge(next(self._edge_ids), start_vertex.id, end_vertex.id, geometry)
        self._edges[e.id] = e
        return e

    def get_edge(self, edge_id: int) -> Edge:
        return self._edges[edge_id]

    def has_edge(self, edge_id: int) -> bool:
        return edge_id in self._edges

    def edges(self) -> List[Edge]:
        return list(self._edges.values())

    # ------------------------- manipulacion ----------------------------- #

    def move_vertex(self, vertex_id: int, new_point: Point2D) -> None:
        """Mueve un vertice y actualiza todas las geometrias conectadas."""
        if vertex_id not in self._vertices:
            return
        self._vertices[vertex_id] = Vertex(vertex_id, new_point)

        for eid, edge in list(self._edges.items()):
            if edge.start_vertex_id == vertex_id or edge.end_vertex_id == vertex_id:
                g = edge.geometry
                v_start = self._vertices[edge.start_vertex_id].point
                v_end = self._vertices[edge.end_vertex_id].point

                if isinstance(g, Line):
                    new_g = Line(v_start, v_end)
                elif isinstance(g, Arc):
                    a0 = math.atan2(v_start.y - g.center.y, v_start.x - g.center.x)
                    a1 = math.atan2(v_end.y - g.center.y, v_end.x - g.center.x)
                    if edge.start_vertex_id == vertex_id:
                        r = g.center.distance_to(v_start)
                    elif edge.end_vertex_id == vertex_id:
                        r = g.center.distance_to(v_end)
                    else:
                        r = g.radius
                    new_g = Arc(g.center, max(r, 1e-6), a0, a1)
                elif isinstance(g, Spline):
                    pts = list(g.points)
                    if edge.start_vertex_id == vertex_id:
                        pts[0] = v_start
                    if edge.end_vertex_id == vertex_id:
                        pts[-1] = v_end
                    new_g = Spline(tuple(pts))
                else:
                    new_g = g

                self._edges[eid] = Edge(eid, edge.start_vertex_id, edge.end_vertex_id, new_g)

    def move_edge_grip(self, edge_id: int, grip_index: int, new_point: Point2D) -> None:
        """Mueve un grip interno (centro de arco, punto interno de spline)."""
        edge = self._edges.get(edge_id)
        if not edge:
            return
        g = edge.geometry

        if isinstance(g, Arc) and grip_index == 0:
            # Trasladar el centro tambien traslada los extremos (mantiene radio)
            delta = Vector2D(new_point.x - g.center.x, new_point.y - g.center.y)
            v_start = self._vertices[edge.start_vertex_id].point + delta
            v_end = self._vertices[edge.end_vertex_id].point + delta
            self._vertices[edge.start_vertex_id] = Vertex(edge.start_vertex_id, v_start)
            self._vertices[edge.end_vertex_id] = Vertex(edge.end_vertex_id, v_end)

            new_g = Arc(new_point, g.radius, g.start_angle, g.end_angle)
            self._edges[edge_id] = Edge(edge_id, edge.start_vertex_id, edge.end_vertex_id, new_g)
        elif isinstance(g, Spline):
            pts = list(g.points)
            pts[grip_index + 1] = new_point
            new_g = Spline(tuple(pts))
            self._edges[edge_id] = Edge(edge_id, edge.start_vertex_id, edge.end_vertex_id, new_g)

    def import_state(self, vertices: Dict[int, Vertex], edges: Dict[int, Edge]) -> None:
        from itertools import count as _count
        self._vertices = dict(vertices)
        self._edges = dict(edges)
        max_v = max(self._vertices.keys(), default=-1)
        max_e = max(self._edges.keys(), default=-1)
        self._vertex_ids = _count(max_v + 1)
        self._edge_ids = _count(max_e + 1)
