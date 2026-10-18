"""Lienzo CAD interactivo basado en QGraphicsView."""

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

    def drawBackground(self, painter: QPainter, rect) -> None:
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
