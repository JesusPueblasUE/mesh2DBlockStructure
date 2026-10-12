"""Lienzo CAD interactivo basado en QGraphicsView."""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen
from PyQt5.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsScene,
    QGraphicsView,
)

from meshcad.core.geometry.point import Point2D
from meshcad.gui.document import Document
from meshcad.gui.items import GeometryItem

VERTEX_RADIUS = 4.0
SNAP_TOLERANCE = 8.0  # en pixeles de pantalla


class CadCanvas(QGraphicsView):
    """Vista grafica donde se dibujan las entidades CAD.

    Delega los eventos de raton en la herramienta activa (si la hay)
    y mantiene un item temporal de vista previa.
    """

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

        self.document.topology_changed.connect(self._redraw_vertices)

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
        """Muestra una geometria temporal (rubber band)."""
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
