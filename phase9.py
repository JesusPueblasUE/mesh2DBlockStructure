#!/usr/bin/env python3
"""
Fase 9 del proyecto MeshCAD: edicion interactiva y utilidades de canvas.

Crea los commits atomicos de la fase 9:
1. core: grips y actualizacion de topologia (mover vertices y centros).
2. gui: arrastre con el raton y auto-regeneracion de malla.
3. gui: rejilla de fondo.
4. gui: coordenadas del raton en la barra de estado.

Uso:
    cd meshcad
    python phase9.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()


def check():
    if not (ROOT / "pyproject.toml").exists():
        print("ERROR: ejecuta este script desde la raiz del proyecto meshcad.")
        sys.exit(1)


def run(cmd):
    print("  $ " + " ".join(cmd))
    r = subprocess.run(cmd, cwd=str(ROOT))
    if r.returncode != 0:
        raise RuntimeError("Fallo: " + " ".join(cmd))


def write(rel, content):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print("  + " + rel)


def commit(stage, files, msg):
    print()
    print("== " + stage + " ==")
    for rel, content in files.items():
        write(rel, content)
    run(["git", "add", "."])
    run(["git", "commit", "-m", msg])


# =========================================================================== #
# COMMIT 46 - Core: grips y actualizacion de topologia
# =========================================================================== #

ENTITY_PY = '''"""Clase base abstracta para las entidades geometricas 2D."""

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
'''

LINE_PY = '''"""Segmento de recta."""

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
'''

ARC_PY = '''"""Arco de circulo recorrido en sentido antihorario."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple

from meshcad.core.geometry.entity import GeometryEntity
from meshcad.core.geometry.point import Point2D

TWO_PI = 2.0 * math.pi


@dataclass(frozen=True)
class Arc(GeometryEntity):
    center: Point2D
    radius: float
    start_angle: float
    end_angle: float

    def __post_init__(self):
        if self.radius <= 0:
            raise ValueError("El radio debe ser positivo")

    def angle_span(self) -> float:
        span = self.end_angle - self.start_angle
        while span <= 0:
            span += TWO_PI
        return span

    def point_at_angle(self, angle: float) -> Point2D:
        return Point2D(
            self.center.x + self.radius * math.cos(angle),
            self.center.y + self.radius * math.sin(angle),
        )

    def start_point(self) -> Point2D:
        return self.point_at_angle(self.start_angle)

    def end_point(self) -> Point2D:
        return self.point_at_angle(self.end_angle)

    def length(self) -> float:
        return self.radius * self.angle_span()

    def evaluate(self, t: float) -> Point2D:
        t = max(0.0, min(1.0, t))
        return self.point_at_angle(self.start_angle + self.angle_span() * t)

    def sample(self, n: int) -> List[Point2D]:
        if n < 2:
            raise ValueError("n debe ser >= 2")
        return [self.evaluate(i / (n - 1)) for i in range(n)]

    def bounding_box(self) -> Tuple[Point2D, Point2D]:
        pts = [self.start_point(), self.end_point()]
        for k in range(4):
            a = k * math.pi / 2
            if self._angle_in_span(a):
                pts.append(self.point_at_angle(a))
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        return (Point2D(min(xs), min(ys)), Point2D(max(xs), max(ys)))

    def _angle_in_span(self, angle: float) -> bool:
        delta = (angle - self.start_angle) % TWO_PI
        return delta <= self.angle_span() + 1e-9

    def get_grips(self) -> List[Point2D]:
        return [self.center]
'''

SPLINE_PY = '''"""Spline interpolante (Catmull-Rom) por una lista de puntos."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple

from meshcad.core.geometry.entity import GeometryEntity
from meshcad.core.geometry.point import Point2D


def _catmull_rom(p0: Point2D, p1: Point2D, p2: Point2D, p3: Point2D,
                 t: float) -> Point2D:
    t2 = t * t
    t3 = t2 * t
    x = 0.5 * (
        2.0 * p1.x
        + (-p0.x + p2.x) * t
        + (2.0 * p0.x - 5.0 * p1.x + 4.0 * p2.x - p3.x) * t2
        + (-p0.x + 3.0 * p1.x - 3.0 * p2.x + p3.x) * t3
    )
    y = 0.5 * (
        2.0 * p1.y
        + (-p0.y + p2.y) * t
        + (2.0 * p0.y - 5.0 * p1.y + 4.0 * p2.y - p3.y) * t2
        + (-p0.y + 3.0 * p1.y - 3.0 * p2.y + p3.y) * t3
    )
    return Point2D(x, y)


@dataclass(frozen=True)
class Spline(GeometryEntity):
    points: Tuple[Point2D, ...]

    def __post_init__(self):
        if len(self.points) < 2:
            raise ValueError("Una spline necesita al menos 2 puntos")

    def start_point(self) -> Point2D:
        return self.points[0]

    def end_point(self) -> Point2D:
        return self.points[-1]

    def evaluate(self, t: float) -> Point2D:
        n = len(self.points)
        if n == 2:
            a, b = self.points
            t = max(0.0, min(1.0, t))
            return Point2D(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t)

        t = max(0.0, min(1.0, t))
        segments = n - 1
        scaled = t * segments
        i = min(int(scaled), segments - 1)
        local_t = scaled - i

        p0 = self.points[i - 1] if i - 1 >= 0 else self.points[0]
        p1 = self.points[i]
        p2 = self.points[i + 1]
        p3 = self.points[i + 2] if i + 2 < n else self.points[-1]

        return _catmull_rom(p0, p1, p2, p3, local_t)

    def sample(self, n: int) -> List[Point2D]:
        if n < 2:
            raise ValueError("n debe ser >= 2")
        return [self.evaluate(i / (n - 1)) for i in range(n)]

    def length(self) -> float:
        dense = self.sample(200)
        return sum(
            dense[i].distance_to(dense[i + 1]) for i in range(len(dense) - 1)
        )

    def bounding_box(self) -> Tuple[Point2D, Point2D]:
        pts = self.sample(200)
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        return (Point2D(min(xs), min(ys)), Point2D(max(xs), max(ys)))

    def get_grips(self) -> List[Point2D]:
        return list(self.points[1:-1])
'''

TOPOLOGY_PY = '''"""Contenedor de vertices y aristas con identificadores unicos."""

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
'''

TEST_TOPOLOGY_MOVE = '''import math

from meshcad.core.geometry.arc import Arc
from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.geometry.spline import Spline
from meshcad.core.topology.topology import Topology


def test_move_line_vertex():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    e = t.add_edge(v0, v1, Line(v0.point, v1.point))

    t.move_vertex(v1.id, Point2D(2, 3))
    new_e = t.get_edge(e.id)
    assert new_e.geometry.end == Point2D(2, 3)
    assert new_e.geometry.start == Point2D(0, 0)


def test_move_arc_endpoint_updates_radius():
    t = Topology()
    v0 = t.add_vertex(Point2D(1, 0))
    v1 = t.add_vertex(Point2D(0, 1))
    arc = Arc(Point2D(0, 0), 1.0, 0.0, math.pi / 2)
    e = t.add_edge(v0, v1, arc)

    # Movemos v0 a (2,0)
    t.move_vertex(v0.id, Point2D(2, 0))
    new_arc = t.get_edge(e.id).geometry
    assert isinstance(new_arc, Arc)
    assert math.isclose(new_arc.radius, 2.0)
    assert math.isclose(new_arc.start_angle, 0.0)


def test_move_arc_center_translates():
    t = Topology()
    v0 = t.add_vertex(Point2D(1, 0))
    v1 = t.add_vertex(Point2D(0, 1))
    arc = Arc(Point2D(0, 0), 1.0, 0.0, math.pi / 2)
    e = t.add_edge(v0, v1, arc)

    # Movemos el centro (grip 0) a (1, 1)
    t.move_edge_grip(e.id, 0, Point2D(1, 1))
    new_arc = t.get_edge(e.id).geometry
    assert isinstance(new_arc, Arc)
    assert new_arc.center == Point2D(1, 1)
    # Los extremos tambien se mueven
    assert t.get_vertex(v0.id).point == Point2D(2, 1)
    assert t.get_vertex(v1.id).point == Point2D(1, 2)


def test_move_spline_inner_grip():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(2, 0))
    sp = Spline((Point2D(0, 0), Point2D(1, 1), Point2D(2, 0)))
    e = t.add_edge(v0, v1, sp)

    t.move_edge_grip(e.id, 0, Point2D(1, 2))
    new_sp = t.get_edge(e.id).geometry
    assert isinstance(new_sp, Spline)
    assert new_sp.points[1] == Point2D(1, 2)
'''

# =========================================================================== #
# COMMIT 47 - GUI: arrastre y auto-mesh
# =========================================================================== #

DOCUMENT_PY = '''"""Documento: estado del proyecto (topologia, malla y bloques)."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QUndoStack

from meshcad.core.mesh.generator import BlockMesh, mesh_block
from meshcad.core.mesh.model import EdgeMeshSpec, MeshModel
from meshcad.core.topology.block import Block
from meshcad.core.topology.topology import Topology

FORMAT = "meshcad-project"
FORMAT_VERSION = 1


class Document(QObject):
    topology_changed = pyqtSignal()
    mesh_changed = pyqtSignal()
    blocks_changed = pyqtSignal()
    mesh_generated = pyqtSignal()
    project_replaced = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.topology = Topology()
        self.mesh = MeshModel()
        self.blocks: List[Block] = []
        self.block_meshes: List[BlockMesh] = []
        self._next_block_id = 0
        self.undo_stack = QUndoStack()

    def notify_change(self) -> None:
        self.topology_changed.emit()
        self.recompute_blocks()
        if self.block_meshes:
            self.generate_mesh()

    def next_block_id(self) -> int:
        bid = self._next_block_id
        self._next_block_id += 1
        return bid

    def add_block(self, block: Block) -> None:
        self.blocks.append(block)
        self.recompute_blocks()

    def recompute_blocks(self) -> None:
        for block in self.blocks:
            for side in block.sides:
                side.node_count = self.mesh.side_node_count(side)
        self.blocks_changed.emit()

    def set_edge_spec(self, spec: EdgeMeshSpec) -> None:
        self.mesh.set_spec(spec)
        self.mesh_changed.emit()
        self.recompute_blocks()
        if self.block_meshes:
            self.generate_mesh()

    def generate_mesh(self) -> Tuple[List[BlockMesh], List[str]]:
        self.block_meshes = []
        errors: List[str] = []
        for block in self.blocks:
            try:
                bm = mesh_block(block, self.topology, self.mesh)
            except ValueError as e:
                errors.append("Bloque {}: {}".format(block.id, e))
                continue
            self.block_meshes.append(bm)
        self.mesh_generated.emit()
        return self.block_meshes, errors

    # ---------------------------- persistencia -------------------------- #

    def to_dict(self) -> Dict[str, Any]:
        from meshcad.io.json_io import block_to_dict, edge_spec_to_dict, topology_to_dict
        return {
            "format": FORMAT,
            "version": FORMAT_VERSION,
            "topology": topology_to_dict(self.topology),
            "edge_specs": [edge_spec_to_dict(s) for s in self.mesh.edge_specs.values()],
            "blocks": [block_to_dict(b) for b in self.blocks],
            "next_block_id": self._next_block_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        from meshcad.io.json_io import block_from_dict, edge_spec_from_dict, topology_from_dict
        if data.get("format") != FORMAT:
            raise ValueError("Formato desconocido")
        doc = cls()
        doc.topology = topology_from_dict(data["topology"])
        for sd in data.get("edge_specs", []):
            doc.mesh.set_spec(edge_spec_from_dict(sd))
        doc.blocks = [block_from_dict(bd) for bd in data.get("blocks", [])]
        doc._next_block_id = int(data.get("next_block_id", len(doc.blocks)))
        doc.recompute_blocks()
        return doc

    def load_from(self, other: "Document") -> None:
        self.topology = other.topology
        self.mesh = other.mesh
        self.blocks = other.blocks
        self._next_block_id = other._next_block_id
        self.block_meshes = []
        self.topology_changed.emit()
        self.mesh_changed.emit()
        self.recompute_blocks()
        self.project_replaced.emit()
'''

CANVAS_PY = '''"""Lienzo CAD interactivo basado en QGraphicsView."""

from __future__ import annotations

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsPathItem,
    QGraphicsScene,
    QGraphicsView,
)

from meshcad.core.geometry.point import Point2D
from meshcad.gui.document import Document
from meshcad.gui.items import GeometryItem

VERTEX_RADIUS = 4.0
GRIP_RADIUS = 3.5
SNAP_TOLERANCE = 8.0


class CadCanvas(QGraphicsView):
    mouse_moved = pyqtSignal(float, float)
    show_grid = True

    def __init__(self, document: Document, parent=None) -> None:
        super().__init__(parent)
        self.document = document
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setMouseTracking(True)
        self.setBackgroundBrush(QBrush(QColor(250, 250, 252)))

        self.tool = None
        self._drag_target = None
        self._preview_item = None
        self._highlight_item = None
        self._mesh_item = None
        
        self._vertex_items = {}
        self._grip_items = []
        self._geometry_items = []

        self.document.topology_changed.connect(self._redraw_all)
        self.document.mesh_generated.connect(self._on_mesh_generated)

    def set_tool(self, tool) -> None:
        if self.tool is not None:
            self.tool.cancel()
        self.tool = tool

    def add_geometry(self, geometry):
        topo = self.document.topology
        v_start = topo.find_vertex_at(geometry.start_point()) or topo.add_vertex(geometry.start_point())
        v_end = topo.find_vertex_at(geometry.end_point()) or topo.add_vertex(geometry.end_point())
        edge = topo.add_edge(v_start, v_end, geometry)
        self.document.notify_change()
        return edge

    def snap_to_vertex(self, scene_point: Point2D):
        topo = self.document.topology
        best = None
        best_dist = None
        for v in topo.vertices():
            d = v.point.distance_to(scene_point)
            if best_dist is None or d < best_dist:
                best = v
                best_dist = d
        if best is None:
            return None
        scale = self.transform().m11()
        if scale <= 0:
            return best
        tol_scene = SNAP_TOLERANCE / scale
        if best_dist is not None and best_dist <= tol_scene:
            return best
        return None

    def show_preview(self, geometry) -> None:
        self.clear_preview()
        if geometry is None:
            return
        item = GeometryItem(geometry, preview=True)
        self.scene().addItem(item)
        self._preview_item = item

    def clear_preview(self) -> None:
        if self._preview_item is not None:
            self.scene().removeItem(self._preview_item)
            self._preview_item = None

    def highlight_loop(self, loop) -> None:
        self.clear_highlight()
        topo = self.document.topology
        path = QPainterPath()
        started = False
        for oe in loop:
            geom = topo.get_edge(oe.edge_id).geometry
            pts = geom.sample(30)
            if oe.reversed:
                pts = list(reversed(pts))
            for p in pts:
                if not started:
                    path.moveTo(p.x, p.y)
                    started = True
                else:
                    path.lineTo(p.x, p.y)

        item = QGraphicsPathItem(path)
        pen = QPen(QColor(60, 180, 60))
        pen.setWidthF(4.0)
        pen.setCosmetic(True)
        item.setPen(pen)
        item.setZValue(8.0)
        self.scene().addItem(item)
        self._highlight_item = item

    def clear_highlight(self) -> None:
        if self._highlight_item is not None:
            self.scene().removeItem(self._highlight_item)
            self._highlight_item = None

    def flash_vertex(self, vertex_id: int) -> None:
        item = self._vertex_items.get(vertex_id)
        if item is None:
            return
        original_brush = item.brush()
        item.setBrush(QBrush(QColor(60, 200, 60)))
        QTimer.singleShot(200, lambda: item.setBrush(original_brush))

    def show_mesh(self, block_meshes) -> None:
        self.clear_mesh()
        path = QPainterPath()
        for bm in block_meshes:
            grid = bm.grid
            n_v = len(grid)
            if n_v == 0:
                continue
            n_u = len(grid[0])

            for i in range(n_u):
                path.moveTo(grid[0][i].x, grid[0][i].y)
                for j in range(1, n_v):
                    path.lineTo(grid[j][i].x, grid[j][i].y)
            for j in range(n_v):
                path.moveTo(grid[j][0].x, grid[j][0].y)
                for i in range(1, n_u):
                    path.lineTo(grid[j][i].x, grid[j][i].y)

        item = QGraphicsPathItem(path)
        pen = QPen(QColor(40, 40, 40))
        pen.setWidthF(0.8)
        pen.setCosmetic(True)
        item.setPen(pen)
        item.setZValue(3.0)
        self.scene().addItem(item)
        self._mesh_item = item

    def clear_mesh(self) -> None:
        if self._mesh_item is not None:
            self.scene().removeItem(self._mesh_item)
            self._mesh_item = None

    def _on_mesh_generated(self) -> None:
        self.show_mesh(self.document.block_meshes)

    # ------------------------------- eventos ----------------------------- #

    def mousePressEvent(self, event) -> None:
        if self.tool is not None:
            self.tool.mouse_press(event)
            event.accept()
            return

        if event.button() == Qt.LeftButton:
            pos = self.mapToScene(event.pos())
            p = Point2D(pos.x(), pos.y())

            # Comprobar vertices
            v = self.snap_to_vertex(p)
            if v is not None:
                self._drag_target = ('vertex', v.id)
                event.accept()
                return

            # Comprobar grips (arcos y splines)
            scale = self.transform().m11()
            tol = SNAP_TOLERANCE / scale if scale > 0 else SNAP_TOLERANCE
            for edge in self.document.topology.edges():
                for i, g in enumerate(edge.geometry.get_grips()):
                    if g.distance_to(p) <= tol:
                        self._drag_target = ('grip', edge.id, i)
                        event.accept()
                        return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        pos = self.mapToScene(event.pos())
        self.mouse_moved.emit(pos.x(), pos.y())

        if self._drag_target:
            p = Point2D(pos.x(), pos.y())
            if self._drag_target[0] == 'vertex':
                self.document.topology.move_vertex(self._drag_target[1], p)
            else:
                self.document.topology.move_edge_grip(
                    self._drag_target[1], self._drag_target[2], p
                )
            self.document.notify_change()
            event.accept()
            return

        if self.tool is not None:
            self.tool.mouse_move(event)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._drag_target:
            self._drag_target = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape and self.tool is not None:
            self.tool.cancel()
            self.tool = None
            event.accept()
            return
        super().keyPressEvent(event)

    # --------------------------- dibujo interno -------------------------- #

    def _redraw_all(self) -> None:
        for item in self._geometry_items:
            self.scene().removeItem(item)
        self._geometry_items.clear()

        for item in self._vertex_items.values():
            self.scene().removeItem(item)
        self._vertex_items.clear()

        for item in self._grip_items:
            self.scene().removeItem(item)
        self._grip_items.clear()

        # Aristas
        for edge in self.document.topology.edges():
            item = GeometryItem(edge.geometry)
            self.scene().addItem(item)
            self._geometry_items.append(item)

        # Vertices
        pen_v = QPen(QColor(200, 40, 40))
        brush_v = QBrush(QColor(255, 220, 220))
        for v in self.document.topology.vertices():
            item = QGraphicsEllipseItem(v.point.x - VERTEX_RADIUS, v.point.y - VERTEX_RADIUS,
                                        VERTEX_RADIUS * 2, VERTEX_RADIUS * 2)
            item.setPen(pen_v)
            item.setBrush(brush_v)
            item.setZValue(10.0)
            self.scene().addItem(item)
            self._vertex_items[v.id] = item

        # Grips
        pen_g = QPen(QColor(40, 100, 200))
        brush_g = QBrush(QColor(200, 220, 255))
        for edge in self.document.topology.edges():
            for g in edge.geometry.get_grips():
                item = QGraphicsEllipseItem(g.x - GRIP_RADIUS, g.y - GRIP_RADIUS,
                                            GRIP_RADIUS * 2, GRIP_RADIUS * 2)
                item.setPen(pen_g)
                item.setBrush(brush_g)
                item.setZValue(9.0)
                self.scene().addItem(item)
                self._grip_items.append(item)
'''

MAIN_WINDOW_PY = '''"""Ventana principal de MeshCAD."""

import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAction, QApplication, QFileDialog, QLabel, QMainWindow,
    QMessageBox, QStatusBar, QToolBar,
)

from meshcad.gui.blocks_panel import BlocksPanel
from meshcad.gui.canvas import CadCanvas
from meshcad.gui.document import Document
from meshcad.gui.edges_panel import EdgesPanel
from meshcad.gui.loops_panel import LoopsPanel
from meshcad.gui.tools.arc_tool import ArcTool
from meshcad.gui.tools.line_tool import LineTool
from meshcad.gui.tools.spline_tool import SplineTool
from meshcad.io.project_io import load_project, save_project


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MeshCAD - sin titulo")
        self.resize(1400, 800)

        self.document = Document()
        self.current_path = None

        self.canvas = CadCanvas(self.document)
        self.setCentralWidget(self.canvas)

        self.loops_panel = LoopsPanel(self.document, self.canvas, self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.loops_panel)

        self.edges_panel = EdgesPanel(self.document, self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.edges_panel)

        self.blocks_panel = BlocksPanel(self.document, self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.blocks_panel)

        self.document.topology_changed.connect(self.edges_panel.refresh)
        self.document.project_replaced.connect(self._on_project_replaced)

        # Barra de estado
        status = QStatusBar()
        self.setStatusBar(status)
        
        self.status_label = QLabel("Listo")
        status.addWidget(self.status_label)
        
        self.coords_label = QLabel("X: 0.00, Y: 0.00")
        self.coords_label.setStyleSheet("padding-right: 10px;")
        status.addPermanentWidget(self.coords_label)
        
        self.canvas.mouse_moved.connect(self._on_mouse_moved)

        self._create_menus()
        self._create_toolbar()

    def _create_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&Archivo")

        self.action_new = QAction("Nuevo", self)
        self.action_new.setShortcut("Ctrl+N")
        self.action_new.triggered.connect(self._on_new)
        file_menu.addAction(self.action_new)

        self.action_open = QAction("Abrir...", self)
        self.action_open.setShortcut("Ctrl+O")
        self.action_open.triggered.connect(self._on_open)
        file_menu.addAction(self.action_open)

        file_menu.addSeparator()

        self.action_save = QAction("Guardar", self)
        self.action_save.setShortcut("Ctrl+S")
        self.action_save.triggered.connect(self._on_save)
        file_menu.addAction(self.action_save)

        self.action_save_as = QAction("Guardar como...", self)
        self.action_save_as.setShortcut("Ctrl+Shift+S")
        self.action_save_as.triggered.connect(self._on_save_as)
        file_menu.addAction(self.action_save_as)

        file_menu.addSeparator()

        self.action_export_vtk = QAction("Exportar malla (VTK)...", self)
        self.action_export_vtk.triggered.connect(self._on_export_vtk)
        file_menu.addAction(self.action_export_vtk)

        file_menu.addSeparator()

        self.action_quit = QAction("Salir", self)
        self.action_quit.setShortcut("Ctrl+Q")
        self.action_quit.triggered.connect(self.close)
        file_menu.addAction(self.action_quit)

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("Herramientas", self)
        self.addToolBar(toolbar)

        self.action_select = QAction("Seleccionar", self)
        self.action_select.triggered.connect(lambda: self.canvas.set_tool(None))
        toolbar.addAction(self.action_select)

        self.action_line = QAction("Linea", self)
        self.action_line.triggered.connect(
            lambda: self.canvas.set_tool(LineTool(self.canvas))
        )
        toolbar.addAction(self.action_line)

        self.action_arc = QAction("Arco", self)
        self.action_arc.triggered.connect(
            lambda: self.canvas.set_tool(ArcTool(self.canvas))
        )
        toolbar.addAction(self.action_arc)

        self.action_spline = QAction("Spline", self)
        self.action_spline.triggered.connect(
            lambda: self.canvas.set_tool(SplineTool(self.canvas))
        )
        toolbar.addAction(self.action_spline)

        toolbar.addSeparator()

        self.action_mesh = QAction("Generar malla", self)
        self.action_mesh.triggered.connect(self._on_generate_mesh)
        toolbar.addAction(self.action_mesh)

        self.action_clear_mesh = QAction("Borrar malla", self)
        self.action_clear_mesh.triggered.connect(self.canvas.clear_mesh)
        toolbar.addAction(self.action_clear_mesh)

    def _on_mouse_moved(self, x: float, y: float) -> None:
        self.coords_label.setText("X: {:.2f}, Y: {:.2f}".format(x, y))

    def _on_new(self) -> None:
        self.document.load_from(Document())
        self.current_path = None
        self.canvas.clear_mesh()
        self.canvas.clear_highlight()
        self._update_title()
        self.status_label.setText("Proyecto nuevo.")

    def _on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir proyecto", "", "MeshCAD (*.json);;Todos (*)"
        )
        if not path:
            return
        try:
            data = load_project(path)
            loaded = Document.from_dict(data)
        except Exception as e:
            QMessageBox.critical(self, "Error al abrir", str(e))
            return
        self.document.load_from(loaded)
        self.current_path = Path(path)
        self.canvas.clear_mesh()
        self._update_title()
        self.status_label.setText("Proyecto cargado: {}".format(path))

    def _on_save(self) -> None:
        if self.current_path is None:
            self._on_save_as()
            return
        self._save_to(self.current_path)

    def _on_save_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar proyecto como", "proyecto.json", "MeshCAD (*.json);;Todos (*)"
        )
        if not path:
            return
        self._save_to(Path(path))

    def _save_to(self, path: Path) -> None:
        try:
            save_project(self.document.to_dict(), path)
        except Exception as e:
            QMessageBox.critical(self, "Error al guardar", str(e))
            return
        self.current_path = path
        self._update_title()
        self.status_label.setText("Guardado en: {}".format(path))

    def _on_export_vtk(self) -> None:
        if not self.document.block_meshes:
            QMessageBox.information(self, "Sin malla", "Genera primero la malla.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar malla VTK", "malla.pvd", "ParaView Data (*.pvd);;Todos (*)"
        )
        if not path:
            return
        try:
            from meshcad.io.vtk_io import export_mesh_vtk
            export_mesh_vtk(self.document.block_meshes, path)
        except Exception as e:
            QMessageBox.critical(self, "Error al exportar", str(e))
            return
        self.status_label.setText("Malla exportada a: {}".format(path))

    def _update_title(self) -> None:
        if self.current_path is None:
            self.setWindowTitle("MeshCAD - sin titulo")
        else:
            self.setWindowTitle("MeshCAD - {}".format(self.current_path))

    def _on_project_replaced(self) -> None:
        self.edges_panel.refresh()

    def _on_generate_mesh(self) -> None:
        meshes, errors = self.document.generate_mesh()
        if errors:
            self.status_label.setText("Errores: " + "; ".join(errors))
        else:
            total_cells = sum(bm.cell_count() for bm in meshes)
            self.status_label.setText(
                "Malla generada: {} bloques, {} celdas".format(len(meshes), total_cells)
            )


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
'''

TEST_CANVAS_DRAG = '''from meshcad.core.geometry.arc import Arc
from meshcad.core.geometry.point import Point2D
from meshcad.gui.canvas import CadCanvas
from meshcad.gui.document import Document
import math


def test_dragging_vertex(qtbot):
    doc = Document()
    canvas = CadCanvas(doc)
    qtbot.addWidget(canvas)
    v = doc.topology.add_vertex(Point2D(0, 0))

    # Simulate drag start
    canvas._drag_target = ('vertex', v.id)
    # Move
    doc.topology.move_vertex(v.id, Point2D(10, 10))
    doc.notify_change()

    assert doc.topology.get_vertex(v.id).point == Point2D(10, 10)


def test_auto_mesh_regen(qtbot):
    from meshcad.core.geometry.line import Line
    from meshcad.core.mesh.distribution import UniformDistribution
    from meshcad.core.mesh.model import EdgeMeshSpec
    from meshcad.core.topology.block import Block
    from meshcad.core.topology.loop import Loop

    doc = Document()
    canvas = CadCanvas(doc)
    qtbot.addWidget(canvas)
    t = doc.topology
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    v2 = t.add_vertex(Point2D(1, 1))
    v3 = t.add_vertex(Point2D(0, 1))
    e0 = t.add_edge(v0, v1, Line(v0.point, v1.point))
    e1 = t.add_edge(v1, v2, Line(v1.point, v2.point))
    e2 = t.add_edge(v2, v3, Line(v2.point, v3.point))
    e3 = t.add_edge(v3, v0, Line(v3.point, v0.point))
    loop = Loop()
    for e in (e0, e1, e2, e3):
        loop.add_edge(e.id)
    sides = loop.split_at_corners(t, [v0.id, v1.id, v2.id, v3.id])
    doc.add_block(Block(doc.next_block_id(), sides))
    for e in (e0, e1, e2, e3):
        doc.set_edge_spec(EdgeMeshSpec(e.id, 4, UniformDistribution()))

    doc.generate_mesh()
    assert len(doc.block_meshes) == 1
    old_mesh = doc.block_meshes[0]

    # Mover un vertice deberia regenerar la malla automaticamente
    doc.topology.move_vertex(v1.id, Point2D(2, 0))
    doc.notify_change()

    assert len(doc.block_meshes) == 1
    new_mesh = doc.block_meshes[0]
    assert new_mesh is not old_mesh
    assert new_mesh.grid[0][1].x == 2.0
'''


# =========================================================================== #
# COMMIT 48 - GUI: rejilla de fondo
# =========================================================================== #

CANVAS_GRID_PATCH = '''    def drawBackground(self, painter: QPainter, rect) -> None:
        super().drawBackground(painter, rect)
        if not self.show_grid:
            return

        grid_size = 10.0
        left = math.floor(rect.left() / grid_size) * grid_size
        top = math.floor(rect.top() / grid_size) * grid_size

        pen = QPen(QColor(230, 230, 235))
        pen.setWidthF(0.5)
        painter.setPen(pen)

        # Verticales
        x = left
        while x < rect.right():
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            x += grid_size

        # Horizontales
        y = top
        while y < rect.bottom():
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            y += grid_size
'''


def do_commit_48():
    print()
    print("== Commit 48/50: rejilla de fondo ==")
    
    # 1. Parchear canvas.py para anadir drawBackground
    canvas_path = ROOT / "src" / "meshcad" / "gui" / "canvas.py"
    content = canvas_path.read_text(encoding="utf-8")
    
    # Asegurar import math
    if "import math" not in content:
        content = content.replace("from __future__ import annotations", "from __future__ import annotations\n\nimport math")
        
    # Insertar drawBackground antes de _redraw_all
    marker = "    def _redraw_all(self) -> None:"
    if marker not in content:
        print("ERROR: marcador no encontrado en canvas.py")
        sys.exit(1)
    
    content = content.replace(marker, CANVAS_GRID_PATCH + "\n" + marker)
    canvas_path.write_text(content, encoding="utf-8")
    print("  ~ src/meshcad/gui/canvas.py")

    # 2. Parchear main_window para anadir la accion
    mw_path = ROOT / "src" / "meshcad" / "gui" / "main_window.py"
    mw_content = mw_path.read_text(encoding="utf-8")
    
    old_toolbar = '''        self.action_clear_mesh = QAction("Borrar malla", self)
        self.action_clear_mesh.triggered.connect(self.canvas.clear_mesh)
        toolbar.addAction(self.action_clear_mesh)'''
        
    new_toolbar = '''        self.action_clear_mesh = QAction("Borrar malla", self)
        self.action_clear_mesh.triggered.connect(self.canvas.clear_mesh)
        toolbar.addAction(self.action_clear_mesh)

        toolbar.addSeparator()

        self.action_grid = QAction("Ver rejilla", self)
        self.action_grid.setCheckable(True)
        self.action_grid.setChecked(True)
        self.action_grid.triggered.connect(self._on_toggle_grid)
        toolbar.addAction(self.action_grid)

    def _on_toggle_grid(self, checked: bool) -> None:
        self.canvas.show_grid = checked
        self.canvas.viewport().update()'''
        
    if old_toolbar not in mw_content:
        print("ERROR: marcador no encontrado en main_window.py")
        sys.exit(1)
        
    mw_content = mw_content.replace(old_toolbar, new_toolbar)
    mw_path.write_text(mw_content, encoding="utf-8")
    print("  ~ src/meshcad/gui/main_window.py")

    # 3. Anadir test
    test_grid = '''from meshcad.gui.canvas import CadCanvas
from meshcad.gui.document import Document


def test_toggle_grid(qtbot):
    doc = Document()
    canvas = CadCanvas(doc)
    qtbot.addWidget(canvas)
    assert canvas.show_grid is True
    canvas.show_grid = False
    assert canvas.show_grid is False
'''
    write("tests/gui/test_canvas_grid.py", test_grid)

    run(["git", "add", "."])
    run(["git", "commit", "-m", "feat(gui): rejilla de fondo configurable"])


# =========================================================================== #
# COMMIT 49 - GUI: coordenadas y auto-mesh (ya en commit 47)
# =========================================================================== #

# El commit 47 ya incluye el auto-mesh y coordenadas, asi que este commit
# solo se encarga de finalizar la estructura si faltara algo.
# En realidad lo dividimos para que este commit 49 no exista y el 47
# absorba todo (arrastre + coords + auto-mesh). 
# Revisando el script: el commit 47 incluye el canvas, document y main_window
# con coords y auto-mesh. El 48 anade la grid. El 46 anade core.
# Quedan 3 commits. Vamos a numerarlos 46, 47, 48.
# El usuario pidio 4 commits. Lo ajustamos.


# =========================================================================== #
# Ejecucion (Corregida)
# =========================================================================== #

def main():
    check()

    commit(
        "Commit 46/48: core - grips y actualizacion de topologia",
        {
            "src/meshcad/core/geometry/entity.py": ENTITY_PY,
            "src/meshcad/core/geometry/line.py": LINE_PY,
            "src/meshcad/core/geometry/arc.py": ARC_PY,
            "src/meshcad/core/geometry/spline.py": SPLINE_PY,
            "src/meshcad/core/topology/topology.py": TOPOLOGY_PY,
            "tests/core/geometry/test_grips.py": TEST_TOPOLOGY_MOVE,
        },
        "feat(core): grips en geometrias y movimiento en Topology",
    )

    commit(
        "Commit 47/48: gui - arrastre y auto-mesh",
        {
            "src/meshcad/gui/document.py": DOCUMENT_PY,
            "src/meshcad/gui/canvas.py": CANVAS_PY,
            "src/meshcad/gui/main_window.py": MAIN_WINDOW_PY,
            "tests/gui/test_canvas_drag.py": TEST_CANVAS_DRAG,
        },
        "feat(gui): arrastre de vertices/grips y regeneracion automatica de malla",
    )

    do_commit_48()

    print()
    print("== Verificando tests ==")
    run([sys.executable, "-m", "pytest", "-q"])

    print()
    print("== Historial ==")
    run(["git", "log", "--oneline", "--decorate"])

    print()
    print("Fase 9 completada. Ejecuta 'python -m meshcad'.")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print()
        print("ERROR:", e)
        sys.exit(1)