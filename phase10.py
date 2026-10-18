#!/usr/bin/env python3
"""
Fase 10 del proyecto MeshCAD: mejoras de canvas y correccion de arcos.

- Fix: Al mover un vertice de un arco, recalcular el centro para que
  la curva siga conectando ambos extremos.
- Feat: Inversion del eje Y (hacia arriba).
- Feat: Zoom con la rueda del raton (centrado en el cursor).
- Feat: Paneo con el boton central del raton.
- Feat: Espaciado de rejilla configurable.

Uso:
    cd meshcad
    python phase10.py
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
# COMMIT 50 - Core: Fix arc update on vertex move
# =========================================================================== #

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
        if not self.has_vertex(start_vertex.id):
            raise ValueError("start_vertex no pertenece a esta topologia")
        if not self.has_vertex(end_vertex.id):
            raise ValueError("end_vertex no pertenece a esta topologia")
        if geometry.start_point().distance_to(start_vertex.point) > TOL:
            raise ValueError("El punto inicial de la geometria no coincide con start_vertex")
        if geometry.end_point().distance_to(end_vertex.point) > TOL:
            raise ValueError("El punto final de la geometria no coincide con end_vertex")
            
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
                    # Recalcular el centro para que el arco pase por ambos extremos.
                    d = v_start.distance_to(v_end)
                    R = g.radius
                    if d > 2 * R:
                        R = d / 2.0
                    h = math.sqrt(max(0.0, R**2 - (d/2)**2))
                    mid = Point2D((v_start.x + v_end.x)/2, (v_start.y + v_end.y)/2)
                    dx, dy = v_end.x - v_start.x, v_end.y - v_start.y
                    nx, ny = -dy, dx
                    norm = math.hypot(nx, ny)
                    if norm > 1e-9:
                        nx, ny = nx/norm, ny/norm
                    else:
                        nx, ny = 0.0, 1.0
                    
                    c1 = Point2D(mid.x + h*nx, mid.y + h*ny)
                    c2 = Point2D(mid.x - h*nx, mid.y - h*ny)
                    # Elegir el centro mas cercano al original para mantener la curvatura
                    new_center = c1 if g.center.distance_to(c1) < g.center.distance_to(c2) else c2
                    
                    a0 = math.atan2(v_start.y - new_center.y, v_start.x - new_center.x)
                    a1 = math.atan2(v_end.y - new_center.y, v_end.x - new_center.x)
                    new_g = Arc(new_center, R, a0, a1)
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

    def __len__(self) -> int:
        return len(self._vertices) + len(self._edges)

    def __repr__(self) -> str:
        return "Topology(vertices={}, edges={})".format(len(self._vertices), len(self._edges))
'''

TEST_TOPOLOGY_FIX = '''import math

from meshcad.core.geometry.arc import Arc
from meshcad.core.geometry.point import Point2D
from meshcad.core.topology.topology import Topology


def test_move_arc_endpoint_reconnects():
    t = Topology()
    v0 = t.add_vertex(Point2D(1, 0))
    v1 = t.add_vertex(Point2D(0, 1))
    arc = Arc(Point2D(0, 0), 1.0, 0.0, math.pi / 2)
    e = t.add_edge(v0, v1, arc)

    # Movemos v0 a (2,0)
    t.move_vertex(v0.id, Point2D(2, 0))
    new_arc = t.get_edge(e.id).geometry
    
    assert isinstance(new_arc, Arc)
    # El arco debe pasar por ambos vertices
    assert math.isclose(new_arc.start_point().distance_to(Point2D(2, 0)), 0.0, abs_tol=1e-7)
    assert math.isclose(new_arc.end_point().distance_to(Point2D(0, 1)), 0.0, abs_tol=1e-7)
'''

# =========================================================================== #
# COMMIT 51 - GUI: Canvas Y-Flip, Zoom, Pan, Grid Spacing
# =========================================================================== #

CANVAS_PY = '''"""Lienzo CAD interactivo basado en QGraphicsView."""

from __future__ import annotations

import math
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
    
    def __init__(self, document: Document, parent=None) -> None:
        super().__init__(parent)
        self.document = document
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setMouseTracking(True)
        self.setBackgroundBrush(QBrush(QColor(250, 250, 252)))
        
        # Invertir eje Y para que crezca hacia arriba
        self.scale(1, -1)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        self.tool = None
        self._drag_target = None
        self._is_panning = False
        self._last_mouse_pos = None
        
        self._preview_item = None
        self._highlight_item = None
        self._mesh_item = None
        
        self.show_grid = True
        self.grid_spacing = 10.0
        
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

    # ---------------------------- eventos ------------------------------- #

    def wheelEvent(self, event) -> None:
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MiddleButton:
            self._is_panning = True
            self._last_mouse_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
            
        if self.tool is not None:
            self.tool.mouse_press(event)
            event.accept()
            return

        if event.button() == Qt.LeftButton:
            pos = self.mapToScene(event.pos())
            p = Point2D(pos.x(), pos.y())

            v = self.snap_to_vertex(p)
            if v is not None:
                self._drag_target = ('vertex', v.id)
                event.accept()
                return

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
        if self._is_panning:
            delta = event.pos() - self._last_mouse_pos
            self._last_mouse_pos = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return

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
        if event.button() == Qt.MiddleButton:
            self._is_panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
            
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

    def drawBackground(self, painter: QPainter, rect) -> None:
        super().drawBackground(painter, rect)
        if not self.show_grid or self.grid_spacing <= 0:
            return

        grid_size = self.grid_spacing
        min_x = math.floor(rect.left() / grid_size) * grid_size
        max_x = math.ceil(rect.right() / grid_size) * grid_size
        min_y = math.floor(min(rect.top(), rect.bottom()) / grid_size) * grid_size
        max_y = math.ceil(max(rect.top(), rect.bottom()) / grid_size) * grid_size

        pen = QPen(QColor(230, 230, 235))
        pen.setWidthF(0.5)
        painter.setPen(pen)

        x = min_x
        while x <= max_x:
            painter.drawLine(int(x), int(min_y), int(x), int(max_y))
            x += grid_size

        y = min_y
        while y <= max_y:
            painter.drawLine(int(min_x), int(y), int(max_x), int(y))
            y += grid_size

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

TEST_CANVAS_V10 = '''from meshcad.gui.canvas import CadCanvas
from meshcad.gui.document import Document
from PyQt5.QtCore import QPoint


def test_y_axis_flip(qtbot):
    doc = Document()
    canvas = CadCanvas(doc)
    qtbot.addWidget(canvas)
    # El eje Y debe ir hacia arriba (transformada escala -1 en Y)
    assert canvas.transform().m22() == -1.0


def test_grid_spacing_property(qtbot):
    doc = Document()
    canvas = CadCanvas(doc)
    qtbot.addWidget(canvas)
    assert canvas.grid_spacing == 10.0
    canvas.grid_spacing = 5.0
    assert canvas.grid_spacing == 5.0
'''

# =========================================================================== #
# COMMIT 52 - GUI: Add grid spacing control to toolbar
# =========================================================================== #

MAIN_WINDOW_PY = '''"""Ventana principal de MeshCAD."""

import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAction, QApplication, QDoubleSpinBox, QFileDialog, QLabel,
    QMainWindow, QMessageBox, QStatusBar, QToolBar,
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

        toolbar.addSeparator()

        self.action_grid = QAction("Ver rejilla", self)
        self.action_grid.setCheckable(True)
        self.action_grid.setChecked(True)
        self.action_grid.triggered.connect(self._on_toggle_grid)
        toolbar.addAction(self.action_grid)

        toolbar.addWidget(QLabel(" Espaciado: "))
        self.grid_spin = QDoubleSpinBox()
        self.grid_spin.setRange(0.1, 100.0)
        self.grid_spin.setValue(10.0)
        self.grid_spin.setSingleStep(1.0)
        self.grid_spin.valueChanged.connect(self._on_grid_spacing_changed)
        toolbar.addWidget(self.grid_spin)

    def _on_toggle_grid(self, checked: bool) -> None:
        self.canvas.show_grid = checked
        self.canvas.viewport().update()

    def _on_grid_spacing_changed(self, value: float) -> None:
        self.canvas.grid_spacing = value
        self.canvas.viewport().update()

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

# =========================================================================== #
# Ejecucion
# =========================================================================== #

def main():
    check()

    commit(
        "Commit 50: Fix arco al mover extremos y actualizar test",
        {
            "src/meshcad/core/topology/topology.py": TOPOLOGY_PY,
            "tests/core/topology/test_grips.py": TEST_TOPOLOGY_FIX,
        },
        "fix(core): recalcular centro del arco para que conecte los extremos movidos",
    )

    commit(
        "Commit 51: Canvas Y-Flip, Zoom y Pan",
        {
            "src/meshcad/gui/canvas.py": CANVAS_PY,
            "tests/gui/test_canvas_v10.py": TEST_CANVAS_V10,
        },
        "feat(gui): invertir eje Y, zoom con rueda y paneo con boton central",
    )

    commit(
        "Commit 52: Espaciado de rejilla",
        {
            "src/meshcad/gui/main_window.py": MAIN_WINDOW_PY,
        },
        "feat(gui): control de espaciado de rejilla en la barra de herramientas",
    )

    print()
    print("== Verificando tests ==")
    run([sys.executable, "-m", "pytest", "-q"])

    print()
    print("== Historial ==")
    run(["git", "log", "--oneline", "--decorate"])

    print()
    print("Fase 10 completada. Ejecuta 'python -m meshcad'.")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print()
        print("ERROR:", e)
        sys.exit(1)