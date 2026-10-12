"""Lienzo CAD interactivo basado en QGraphicsView."""

from __future__ import annotations

from PyQt5.QtCore import Qt, QTimer
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
SNAP_TOLERANCE = 8.0


class CadCanvas(QGraphicsView):
    def __init__(self, document: Document, parent=None) -> None:
        super().__init__(parent)
        self.document = document
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setMouseTracking(True)
        self.setBackgroundBrush(QBrush(QColor(250, 250, 252)))

        self.tool = None
        self._vertex_items = {}
        self._preview_item = None
        self._highlight_item = None
        self._mesh_item = None

        self.document.topology_changed.connect(self._redraw_vertices)
        self.document.mesh_generated.connect(self._on_mesh_generated)

    # ----------------------------- API publica --------------------------- #

    def set_tool(self, tool) -> None:
        if self.tool is not None:
            self.tool.cancel()
        self.tool = tool

    def add_geometry(self, geometry):
        topo = self.document.topology
        v_start = topo.find_vertex_at(geometry.start_point())
        if v_start is None:
            v_start = topo.add_vertex(geometry.start_point())
        v_end = topo.find_vertex_at(geometry.end_point())
        if v_end is None:
            v_end = topo.add_vertex(geometry.end_point())
        edge = topo.add_edge(v_start, v_end, geometry)
        item = GeometryItem(geometry)
        self.scene().addItem(item)
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

    # ----------------------------- preview ------------------------------- #

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

    # ---------------------------- highlight ------------------------------ #

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

    # ------------------------------ mesh --------------------------------- #

    def show_mesh(self, block_meshes) -> None:
        """Dibuja las mallas de los bloques como lineas finas."""
        self.clear_mesh()
        path = QPainterPath()
        for bm in block_meshes:
            grid = bm.grid
            n_v = len(grid)
            if n_v == 0:
                continue
            n_u = len(grid[0])

            # Lineas verticales (columnas)
            for i in range(n_u):
                path.moveTo(grid[0][i].x, grid[0][i].y)
                for j in range(1, n_v):
                    path.lineTo(grid[j][i].x, grid[j][i].y)
            # Lineas horizontales (filas)
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
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self.tool is not None:
            self.tool.mouse_move(event)
        super().mouseMoveEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape and self.tool is not None:
            self.tool.cancel()
            self.tool = None
            event.accept()
            return
        super().keyPressEvent(event)

    # --------------------------- dibujo interno -------------------------- #

    def _redraw_vertices(self) -> None:
        for item in self._vertex_items.values():
            self.scene().removeItem(item)
        self._vertex_items.clear()

        pen = QPen(QColor(200, 40, 40))
        pen.setWidthF(1.0)
        brush = QBrush(QColor(255, 220, 220))
        for v in self.document.topology.vertices():
            item = QGraphicsEllipseItem(
                v.point.x - VERTEX_RADIUS,
                v.point.y - VERTEX_RADIUS,
                2 * VERTEX_RADIUS,
                2 * VERTEX_RADIUS,
            )
            item.setPen(pen)
            item.setBrush(brush)
            item.setZValue(10.0)
            self.scene().addItem(item)
            self._vertex_items[v.id] = item
