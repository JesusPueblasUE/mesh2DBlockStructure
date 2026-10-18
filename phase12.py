#!/usr/bin/env python3
"""
Fase 12: Seleccion con raton, reset zoom y propagacion de nodos.
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
# COMMIT 56 - Propagacion de nodos en Document
# =========================================================================== #

DOCUMENT_PY = '''"""Documento: estado del proyecto (topologia, malla y bloques)."""

from __future__ import annotations
from typing import Any, Dict, List, Tuple

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QUndoStack

from meshcad.core.mesh.generator import BlockMesh, mesh_block
from meshcad.core.mesh.model import EdgeMeshSpec, MeshModel, UniformDistribution
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

    def remove_block(self, block_id: int) -> None:
        self.blocks = [b for b in self.blocks if b.id != block_id]
        self.recompute_blocks()
        if self.block_meshes:
            self.generate_mesh()
        self.blocks_changed.emit()

    def remove_edges(self, edge_ids: list) -> tuple:
        success = 0
        fail = 0
        for eid in edge_ids:
            in_block = False
            for b in self.blocks:
                for side in b.sides:
                    if eid in side.edge_ids():
                        in_block = True
                        break
                if in_block:
                    break
            
            if in_block:
                fail += 1
            else:
                self.topology.remove_edge(eid)
                self.mesh.clear_spec(eid)
                success += 1
                
        if success > 0:
            self.notify_change()
        return success, fail

    def recompute_blocks(self) -> None:
        for block in self.blocks:
            for side in block.sides:
                side.node_count = self.mesh.side_node_count(side)
        self.blocks_changed.emit()

    # ------------------------------- mesh ------------------------------- #

    def _propagate_nodes(self, edge_id: int, n_nodes: int, visited: set) -> None:
        if edge_id in visited:
            return
        visited.add(edge_id)

        spec = self.mesh.get_spec(edge_id)
        self.mesh.set_spec(EdgeMeshSpec(edge_id, n_nodes, spec.distribution))

        for block in self.blocks:
            for i, side in enumerate(block.sides):
                if edge_id in side.edge_ids():
                    opp_idx = (i + 2) % 4
                    opp_side = block.sides[opp_idx]
                    k = len(opp_side.oriented_edges)
                    if k > 0:
                        base = (n_nodes + k - 1) // k
                        for oe in opp_side.oriented_edges:
                            self._propagate_nodes(oe.edge_id, base, visited)

    def set_edge_spec(self, spec: EdgeMeshSpec) -> None:
        visited = set()
        self._propagate_nodes(spec.edge_id, spec.n_nodes, visited)
        # Asegurarnos de que la arista original mantiene su distribucion
        self.mesh.set_spec(spec)
        self.mesh_changed.emit()
        self.recompute_blocks()
        if self.block_meshes:
            self.generate_mesh()

    def set_edge_specs(self, specs: List[EdgeMeshSpec]) -> None:
        visited = set()
        for spec in specs:
            self._propagate_nodes(spec.edge_id, spec.n_nodes, visited)
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

# =========================================================================== #
# COMMIT 57 - Canvas: Click selection y reset zoom
# =========================================================================== #

CANVAS_PY = '''"""Lienzo CAD interactivo basado en QGraphicsView."""

from __future__ import annotations
import math
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import (
    QGraphicsEllipseItem, QGraphicsPathItem, QGraphicsScene, QGraphicsView, 
    QDialog, QVBoxLayout, QFormLayout, QDoubleSpinBox, QDialogButtonBox
)
from meshcad.core.geometry.point import Point2D
from meshcad.gui.document import Document
from meshcad.gui.items import GeometryItem

VERTEX_RADIUS = 4.0
GRIP_RADIUS = 3.5
SNAP_TOLERANCE = 8.0


class CadCanvas(QGraphicsView):
    mouse_moved = pyqtSignal(float, float)
    edge_clicked = pyqtSignal(int)
    
    def __init__(self, document: Document, parent=None) -> None:
        super().__init__(parent)
        self.document = document
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setMouseTracking(True)
        self.setBackgroundBrush(QBrush(QColor(250, 250, 252)))
        
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

    def reset_zoom(self) -> None:
        self.resetTransform()
        self.scale(1, -1)

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

    def highlight_edges(self, edge_ids: list) -> None:
        self.clear_highlight()
        if not edge_ids:
            return
        path = QPainterPath()
        topo = self.document.topology
        for eid in edge_ids:
            geom = topo.get_edge(eid).geometry
            pts = geom.sample(30)
            path.moveTo(pts[0].x, pts[0].y)
            for p in pts[1:]:
                path.lineTo(p.x, p.y)
                
        item = QGraphicsPathItem(path)
        pen = QPen(QColor(240, 140, 20))
        pen.setWidthF(3.0)
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
            if n_v == 0: continue
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

            # Deteccion de clic en arista
            items = self.items(event.pos())
            for item in items:
                if isinstance(item, GeometryItem) and hasattr(item, 'edge_id'):
                    self.edge_clicked.emit(item.edge_id)
                    event.accept()
                    return

            self.clear_highlight()
            self.edge_clicked.emit(-1)

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.LeftButton and self.tool is None:
            pos = self.mapToScene(event.pos())
            p = Point2D(pos.x(), pos.y())
            v = self.snap_to_vertex(p)
            if v is not None:
                dialog = QDialog(self)
                dialog.setWindowTitle("Editar coordenadas")
                layout = QVBoxLayout(dialog)
                form = QFormLayout()
                spin_x = QDoubleSpinBox()
                spin_x.setRange(-999999, 999999)
                spin_x.setDecimals(4)
                spin_x.setValue(v.point.x)
                spin_y = QDoubleSpinBox()
                spin_y.setRange(-999999, 999999)
                spin_y.setDecimals(4)
                spin_y.setValue(v.point.y)
                form.addRow("X:", spin_x)
                form.addRow("Y:", spin_y)
                layout.addLayout(form)
                buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
                buttons.accepted.connect(dialog.accept)
                buttons.rejected.connect(dialog.reject)
                layout.addWidget(buttons)
                
                if dialog.exec_() == QDialog.Accepted:
                    new_p = Point2D(spin_x.value(), spin_y.value())
                    self.document.topology.move_vertex(v.id, new_p)
                    self.document.notify_change()
                event.accept()
                return
        super().mouseDoubleClickEvent(event)

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
                self.document.topology.move_edge_grip(self._drag_target[1], self._drag_target[2], p)
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
        for item in self._geometry_items: self.scene().removeItem(item)
        self._geometry_items.clear()
        for item in self._vertex_items.values(): self.scene().removeItem(item)
        self._vertex_items.clear()
        for item in self._grip_items: self.scene().removeItem(item)
        self._grip_items.clear()

        for edge in self.document.topology.edges():
            item = GeometryItem(edge.geometry)
            item.edge_id = edge.id
            self.scene().addItem(item)
            self._geometry_items.append(item)

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

# =========================================================================== #
# COMMIT 58 - GUI: Integracion de eventos en EdgesPanel y MainWindow
# =========================================================================== #

EDGES_PANEL_PY = '''"""Panel para editar la especificacion de malla de cada arista."""

from __future__ import annotations
from PyQt5.QtWidgets import (
    QComboBox, QDockWidget, QDoubleSpinBox, QFormLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton, QSpinBox, QVBoxLayout, QWidget, QAbstractItemView
)
from meshcad.core.mesh.distribution import BiasedDistribution, UniformDistribution
from meshcad.core.mesh.model import EdgeMeshSpec
from meshcad.gui.document import Document


class EdgesPanel(QDockWidget):
    def __init__(self, document: Document, canvas, parent=None) -> None:
        super().__init__("Distribuciones", parent)
        self.document = document
        self.canvas = canvas

        container = QWidget()
        layout = QVBoxLayout(container)

        self.refresh_button = QPushButton("Refrescar aristas")
        self.refresh_button.clicked.connect(self.refresh)
        layout.addWidget(self.refresh_button)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.list_widget)

        form = QFormLayout()
        self.nodes_spin = QSpinBox()
        self.nodes_spin.setRange(2, 10000)
        self.nodes_spin.setValue(5)
        form.addRow("Nodos:", self.nodes_spin)

        self.dist_combo = QComboBox()
        self.dist_combo.addItems(["Uniforme", "Sesgada"])
        self.dist_combo.currentIndexChanged.connect(self._on_dist_changed)
        form.addRow("Distribucion:", self.dist_combo)

        self.bias_spin = QDoubleSpinBox()
        self.bias_spin.setRange(0.01, 100.0)
        self.bias_spin.setValue(2.0)
        self.bias_spin.setSingleStep(0.1)
        self.bias_spin.setEnabled(False)
        form.addRow("Bias:", self.bias_spin)
        layout.addLayout(form)

        self.apply_button = QPushButton("Aplicar a seleccionadas")
        self.apply_button.clicked.connect(self._on_apply)
        layout.addWidget(self.apply_button)
        
        self.delete_button = QPushButton("Eliminar arista(s) seleccionada(s)")
        self.delete_button.clicked.connect(self._on_delete)
        layout.addWidget(self.delete_button)

        self.status = QLabel("Refresca para ver las aristas.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.setWidget(container)

    def select_edges(self, edge_ids: list) -> None:
        self.list_widget.blockSignals(True)
        self.list_widget.clearSelection()
        edges = self.document.topology.edges()
        
        for item_idx in range(self.list_widget.count()):
            item = self.list_widget.item(item_idx)
            if 0 <= item_idx < len(edges) and edges[item_idx].id in edge_ids:
                item.setSelected(True)
                
        self.list_widget.blockSignals(False)
        self._on_selection_changed()

    def refresh(self) -> None:
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for edge in self.document.topology.edges():
            spec = self.document.mesh.get_spec(edge.id)
            label = "Edge {}: v{}->v{}, {} nodos, {}".format(
                edge.id, edge.start_vertex_id, edge.end_vertex_id, spec.n_nodes, self._dist_name(spec.distribution)
            )
            self.list_widget.addItem(QListWidgetItem(label))
        self.list_widget.blockSignals(False)
        
        if self.list_widget.count() == 0:
            self.status.setText("No hay aristas todavia.")
        else:
            self.status.setText("{} aristas. Selecciona una o varias.".format(self.list_widget.count()))

    def _on_selection_changed(self) -> None:
        selected_items = self.list_widget.selectedItems()
        edge_ids = []
        edges = self.document.topology.edges()
        
        for item in selected_items:
            row = self.list_widget.row(item)
            if 0 <= row < len(edges):
                edge_ids.append(edges[row].id)
                
        self.canvas.highlight_edges(edge_ids)

        if len(selected_items) == 1:
            row = self.list_widget.row(selected_items[0])
            spec = self.document.mesh.get_spec(edges[row].id)
            self.nodes_spin.setValue(spec.n_nodes)
            if isinstance(spec.distribution, BiasedDistribution):
                self.dist_combo.setCurrentText("Sesgada")
                self.bias_spin.setValue(spec.distribution.bias)
                self.bias_spin.setEnabled(True)
            else:
                self.dist_combo.setCurrentText("Uniforme")
                self.bias_spin.setEnabled(False)

    def _on_dist_changed(self, index: int) -> None:
        self.bias_spin.setEnabled(index == 1)

    def _on_apply(self) -> None:
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            self.status.setText("Selecciona primero alguna arista.")
            return
            
        edges = self.document.topology.edges()
        specs = []
        for item in selected_items:
            row = self.list_widget.row(item)
            if 0 <= row < len(edges):
                edge = edges[row]
                if self.dist_combo.currentText() == "Sesgada":
                    dist = BiasedDistribution(bias=self.bias_spin.value())
                else:
                    dist = UniformDistribution()
                specs.append(EdgeMeshSpec(edge.id, self.nodes_spin.value(), dist))
                
        self.document.set_edge_specs(specs)
        self.refresh()
        self.status.setText("{} aristas actualizadas.".format(len(specs)))

    def _on_delete(self) -> None:
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return
            
        edges = self.document.topology.edges()
        edge_ids_to_delete = []
        for item in selected_items:
            row = self.list_widget.row(item)
            if 0 <= row < len(edges):
                edge_ids_to_delete.append(edges[row].id)
                
        self.canvas.clear_highlight()

        success, fail = self.document.remove_edges(edge_ids_to_delete)
        self.refresh()
        
        if fail > 0:
            self.status.setText("{} aristas borradas. {} no se pudieron borrar porque pertenecen a un bloque.".format(success, fail))
        else:
            self.status.setText("{} aristas borradas.".format(success))

    @staticmethod
    def _dist_name(dist):
        if isinstance(dist, BiasedDistribution):
            return "sesgada({:g})".format(dist.bias)
        return "uniforme"
'''

MAIN_WINDOW_PY = '''"""Ventana principal de MeshCAD."""

import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAction, QApplication, QDoubleSpinBox, QFileDialog, QLabel,
    QMainWindow, QMessageBox, QStatusBar, QToolBar, QDialog, 
    QVBoxLayout, QFormLayout, QDialogButtonBox
)

from meshcad.core.geometry.point import Point2D
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

        self.edges_panel = EdgesPanel(self.document, self.canvas, self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.edges_panel)

        self.blocks_panel = BlocksPanel(self.document, self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.blocks_panel)

        self.document.topology_changed.connect(self.edges_panel.refresh)
        self.document.project_replaced.connect(self._on_project_replaced)
        self.canvas.edge_clicked.connect(self._on_edge_clicked)

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

    def _on_edge_clicked(self, edge_id: int) -> None:
        if edge_id == -1:
            self.edges_panel.list_widget.clearSelection()
        else:
            self.edges_panel.select_edges([edge_id])

    def _create_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&Archivo")
        self.action_new = QAction("Nuevo", self)
        self.action_new.triggered.connect(self._on_new)
        file_menu.addAction(self.action_new)
        self.action_open = QAction("Abrir...", self)
        self.action_open.triggered.connect(self._on_open)
        file_menu.addAction(self.action_open)
        file_menu.addSeparator()
        self.action_save = QAction("Guardar", self)
        self.action_save.triggered.connect(self._on_save)
        file_menu.addAction(self.action_save)
        self.action_save_as = QAction("Guardar como...", self)
        self.action_save_as.triggered.connect(self._on_save_as)
        file_menu.addAction(self.action_save_as)
        file_menu.addSeparator()
        self.action_export_vtk = QAction("Exportar malla (VTK)...", self)
        self.action_export_vtk.triggered.connect(self._on_export_vtk)
        file_menu.addAction(self.action_export_vtk)
        file_menu.addSeparator()
        self.action_quit = QAction("Salir", self)
        self.action_quit.triggered.connect(self.close)
        file_menu.addAction(self.action_quit)

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("Herramientas", self)
        self.addToolBar(toolbar)

        self.action_select = QAction("Seleccionar", self)
        self.action_select.triggered.connect(lambda: self.canvas.set_tool(None))
        toolbar.addAction(self.action_select)

        self.action_line = QAction("Linea", self)
        self.action_line.triggered.connect(lambda: self.canvas.set_tool(LineTool(self.canvas)))
        toolbar.addAction(self.action_line)

        self.action_arc = QAction("Arco", self)
        self.action_arc.triggered.connect(lambda: self.canvas.set_tool(ArcTool(self.canvas)))
        toolbar.addAction(self.action_arc)

        self.action_spline = QAction("Spline", self)
        self.action_spline.triggered.connect(lambda: self.canvas.set_tool(SplineTool(self.canvas)))
        toolbar.addAction(self.action_spline)
        
        self.action_insert_point = QAction("Insertar Punto", self)
        self.action_insert_point.triggered.connect(self._on_insert_point)
        toolbar.addAction(self.action_insert_point)

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
        self.grid_spin.valueChanged.connect(self._on_grid_spacing_changed)
        toolbar.addWidget(self.grid_spin)

        toolbar.addSeparator()
        self.action_reset_zoom = QAction("Reset Zoom", self)
        self.action_reset_zoom.triggered.connect(self.canvas.reset_zoom)
        toolbar.addAction(self.action_reset_zoom)

    def _on_insert_point(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Insertar punto")
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        spin_x = QDoubleSpinBox()
        spin_x.setRange(-999999, 999999)
        spin_x.setDecimals(4)
        spin_x.setValue(0)
        spin_y = QDoubleSpinBox()
        spin_y.setRange(-999999, 999999)
        spin_y.setDecimals(4)
        spin_y.setValue(0)
        form.addRow("X:", spin_x)
        form.addRow("Y:", spin_y)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            self.document.topology.add_vertex(Point2D(spin_x.value(), spin_y.value()))
            self.document.notify_change()

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
        path, _ = QFileDialog.getOpenFileName(self, "Abrir proyecto", "", "MeshCAD (*.json);;Todos (*)")
        if not path: return
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
        if self.current_path is None: self._on_save_as()
        else: self._save_to(self.current_path)

    def _on_save_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Guardar como", "proyecto.json", "MeshCAD (*.json);;Todos (*)")
        if path: self._save_to(Path(path))

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
        path, _ = QFileDialog.getSaveFileName(self, "Exportar VTK", "malla.pvd", "ParaView (*.pvd);;Todos (*)")
        if not path: return
        try:
            from meshcad.io.vtk_io import export_mesh_vtk
            export_mesh_vtk(self.document.block_meshes, path)
        except Exception as e:
            QMessageBox.critical(self, "Error al exportar", str(e))
            return
        self.status_label.setText("Malla exportada a: {}".format(path))

    def _update_title(self) -> None:
        if self.current_path is None: self.setWindowTitle("MeshCAD - sin titulo")
        else: self.setWindowTitle("MeshCAD - {}".format(self.current_path))

    def _on_project_replaced(self) -> None:
        self.edges_panel.refresh()

    def _on_generate_mesh(self) -> None:
        meshes, errors = self.document.generate_mesh()
        if errors:
            self.status_label.setText("Errores: " + "; ".join(errors))
        else:
            total_cells = sum(bm.cell_count() for bm in meshes)
            self.status_label.setText("Malla generada: {} bloques, {} celdas".format(len(meshes), total_cells))


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
'''


def main():
    check()

    commit(
        "Commit 56: Propagacion de nodos en Document",
        {
            "src/meshcad/gui/document.py": DOCUMENT_PY,
        },
        "feat(core): propagacion recursiva de nodos a lados opuestos",
    )

    commit(
        "Commit 57: Seleccion con raton y reset zoom en Canvas",
        {
            "src/meshcad/gui/canvas.py": CANVAS_PY,
        },
        "feat(gui): seleccion de aristas con el raton y reset zoom",
    )

    commit(
        "Commit 58: Integracion de eventos en EdgesPanel y MainWindow",
        {
            "src/meshcad/gui/edges_panel.py": EDGES_PANEL_PY,
            "src/meshcad/gui/main_window.py": MAIN_WINDOW_PY,
        },
        "feat(gui): sincronizar seleccion entre canvas y panel, anadir reset zoom",
    )

    print("\n== Verificando tests ==")
    run([sys.executable, "-m", "pytest", "-q"])
    
    print("\n== Historial ==")
    run(["git", "log", "--oneline", "-n", "3"])

if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print("\nERROR:", e)
        sys.exit(1)