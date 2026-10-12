#!/usr/bin/env python3
"""
Vista previa en tiempo real para las herramientas CAD.

Anade rubber-band preview a LineTool, ArcTool y SplineTool.

Uso:
    cd meshcad
    python phase3_preview.py
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
# COMMIT 16 - Infraestructura de preview
# =========================================================================== #

ITEMS_PY = '''"""Items graficos que representan entidades geometricas en la escena."""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainterPath, QPen
from PyQt5.QtWidgets import QGraphicsPathItem

from meshcad.core.geometry.entity import GeometryEntity

SAMPLE_COUNT = 60


def _build_path(geometry: GeometryEntity) -> QPainterPath:
    path = QPainterPath()
    pts = geometry.sample(SAMPLE_COUNT)
    if not pts:
        return path
    path.moveTo(pts[0].x, pts[0].y)
    for p in pts[1:]:
        path.lineTo(p.x, p.y)
    return path


class GeometryItem(QGraphicsPathItem):
    """Item QGraphics que dibuja una entidad geometrica.

    En modo preview la pluma es discontinua y clara, no es seleccionable
    y tiene un z-value menor para que quede por debajo de la geometria real.
    """

    def __init__(self, geometry: GeometryEntity, preview: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.geometry = geometry
        self.setPath(_build_path(geometry))

        if preview:
            pen = QPen(QColor(90, 150, 220))
            pen.setWidthF(1.5)
            pen.setCosmetic(True)
            pen.setStyle(Qt.DashLine)
            self.setZValue(5.0)
        else:
            pen = QPen(QColor(30, 90, 200))
            pen.setWidthF(2.0)
            pen.setCosmetic(True)
            self.setFlag(QGraphicsPathItem.ItemIsSelectable, True)
            self.setZValue(0.0)

        self.setPen(pen)
'''

CANVAS_PY = '''"""Lienzo CAD interactivo basado en QGraphicsView."""

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
'''

TOOLS_BASE_PY = '''"""Clase base de las herramientas interactivas."""

from __future__ import annotations

from typing import List

from meshcad.core.geometry.point import Point2D


class BaseTool:
    """Interfaz comun a todas las herramientas interactivas.

    Cada herramienta acumula puntos en self.points. Cuando tiene
    suficientes, llama a canvas.add_geometry. Mientras tanto muestra
    una vista previa llamando a canvas.show_preview.
    """

    def __init__(self, canvas) -> None:
        self.canvas = canvas
        self.points: List[Point2D] = []

    def mouse_press(self, event) -> None:  # pragma: no cover - abstracto
        raise NotImplementedError

    def mouse_move(self, event) -> None:
        self._refresh_preview(event)

    def cancel(self) -> None:
        self.points = []
        self.canvas.clear_preview()

    # ----------------------- utilidades para subclases ------------------ #

    def _scene_point(self, event) -> Point2D:
        pos = self.canvas.mapToScene(event.pos())
        p = Point2D(pos.x(), pos.y())
        snapped = self.canvas.snap_to_vertex(p)
        if snapped is not None:
            return snapped.point
        return p

    def _refresh_preview(self, event) -> None:
        """Sobrescrito por cada herramienta."""
        return None
'''

# =========================================================================== #
# COMMIT 17 - Preview en LineTool y ArcTool
# =========================================================================== #

TOOLS_LINE_PY = '''"""Herramienta interactiva para dibujar segmentos de recta."""

from __future__ import annotations

from meshcad.core.geometry.line import Line
from meshcad.gui.tools.base import BaseTool


class LineTool(BaseTool):
    """Dos clics: inicio y fin. Muestra la recta en tiempo real."""

    def mouse_press(self, event) -> None:
        p = self._scene_point(event)
        self.points.append(p)

        if len(self.points) == 2:
            self.canvas.add_geometry(Line(self.points[0], self.points[1]))
            self.points = []
            self.canvas.clear_preview()
        else:
            self._refresh_preview(event)

    def _refresh_preview(self, event) -> None:
        if not self.points:
            self.canvas.clear_preview()
            return
        p = self._scene_point(event)
        self.canvas.show_preview(Line(self.points[0], p))
'''

TOOLS_ARC_PY = '''"""Herramienta interactiva para dibujar arcos de circulo."""

from __future__ import annotations

import math

from meshcad.core.geometry.arc import Arc
from meshcad.gui.tools.base import BaseTool

EPS = 1e-9


class ArcTool(BaseTool):
    """Tres clics: centro, inicio, fin. Arco CCW con vista previa.

    - Con 1 punto (centro) muestra el circulo con radio = distancia al raton.
    - Con 2 puntos (centro, inicio) muestra el arco hasta el raton.
    """

    def mouse_press(self, event) -> None:
        p = self._scene_point(event)
        self.points.append(p)

        if len(self.points) == 3:
            center, start, end = self.points
            radius = center.distance_to(start)
            if radius > EPS:
                a0 = math.atan2(start.y - center.y, start.x - center.x)
                a1 = math.atan2(end.y - center.y, end.x - center.x)
                self.canvas.add_geometry(Arc(center, radius, a0, a1))
            self.points = []
            self.canvas.clear_preview()
        else:
            self._refresh_preview(event)

    def _refresh_preview(self, event) -> None:
        if not self.points:
            self.canvas.clear_preview()
            return

        p = self._scene_point(event)

        if len(self.points) == 1:
            center = self.points[0]
            r = center.distance_to(p)
            if r < EPS:
                self.canvas.clear_preview()
                return
            # Circulo completo como casi-2pi
            self.canvas.show_preview(Arc(center, r, 0.0, 2.0 * math.pi - 1e-6))
            return

        # len == 2
        center, start = self.points
        r = center.distance_to(start)
        if r < EPS:
            self.canvas.clear_preview()
            return
        a0 = math.atan2(start.y - center.y, start.x - center.x)
        a1 = math.atan2(p.y - center.y, p.x - center.x)
        self.canvas.show_preview(Arc(center, r, a0, a1))
'''

TEST_LINE_TOOL = '''from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.gui.tools.line_tool import LineTool


class FakeCanvas:
    def __init__(self):
        self.geometries = []
        self.previews = []
        self.cleared = 0

    def add_geometry(self, geometry):
        self.geometries.append(geometry)

    def snap_to_vertex(self, p):
        return None

    def show_preview(self, geometry):
        self.previews.append(geometry)

    def clear_preview(self):
        self.cleared += 1


class FakeMouseEvent:
    def __init__(self, x, y):
        self._pos = (x, y)

    def pos(self):
        from PyQt5.QtCore import QPoint

        return QPoint(self._pos[0], self._pos[1])


def make_canvas():
    c = FakeCanvas()
    c.mapToScene = lambda qpoint: qpoint  # type: ignore[attr-defined]
    return c


def test_line_tool_creates_line_after_two_clicks():
    canvas = make_canvas()
    tool = LineTool(canvas)
    tool.mouse_press(FakeMouseEvent(0, 0))
    tool.mouse_press(FakeMouseEvent(10, 5))
    assert len(canvas.geometries) == 1
    geom = canvas.geometries[0]
    assert isinstance(geom, Line)
    assert geom.start == Point2D(0, 0)
    assert geom.end == Point2D(10, 5)


def test_line_tool_preview_after_first_click():
    canvas = make_canvas()
    tool = LineTool(canvas)
    tool.mouse_press(FakeMouseEvent(0, 0))
    # Tras el primer clic debe existir un preview
    assert len(canvas.previews) == 1
    # Mover el raton actualiza el preview
    tool.mouse_move(FakeMouseEvent(5, 5))
    assert len(canvas.previews) == 2
    assert canvas.previews[-1].end == Point2D(5, 5)


def test_line_tool_clears_preview_after_completion():
    canvas = make_canvas()
    tool = LineTool(canvas)
    tool.mouse_press(FakeMouseEvent(0, 0))
    cleared_before = canvas.cleared
    tool.mouse_press(FakeMouseEvent(10, 0))
    assert canvas.cleared > cleared_before


def test_line_tool_cancel_clears_preview():
    canvas = make_canvas()
    tool = LineTool(canvas)
    tool.mouse_press(FakeMouseEvent(0, 0))
    tool.cancel()
    assert tool.points == []
    assert canvas.cleared >= 1
'''

TEST_ARC_TOOL = '''import math

from meshcad.core.geometry.arc import Arc
from meshcad.gui.tools.arc_tool import ArcTool


class FakeCanvas:
    def __init__(self):
        self.geometries = []
        self.previews = []
        self.cleared = 0

    def add_geometry(self, geometry):
        self.geometries.append(geometry)

    def snap_to_vertex(self, p):
        return None

    def show_preview(self, geometry):
        self.previews.append(geometry)

    def clear_preview(self):
        self.cleared += 1


class FakeMouseEvent:
    def __init__(self, x, y):
        self._pos = (x, y)

    def pos(self):
        from PyQt5.QtCore import QPoint

        return QPoint(self._pos[0], self._pos[1])


def make_canvas():
    c = FakeCanvas()
    c.mapToScene = lambda qpoint: qpoint  # type: ignore[attr-defined]
    return c


def test_arc_tool_creates_arc_after_three_clicks():
    canvas = make_canvas()
    tool = ArcTool(canvas)
    tool.mouse_press(FakeMouseEvent(0, 0))
    tool.mouse_press(FakeMouseEvent(1, 0))
    tool.mouse_press(FakeMouseEvent(0, 1))
    assert len(canvas.geometries) == 1
    arc = canvas.geometries[0]
    assert isinstance(arc, Arc)
    assert math.isclose(arc.radius, 1.0)
    assert math.isclose(arc.start_angle, 0.0)
    assert math.isclose(arc.end_angle, math.pi / 2)


def test_arc_tool_preview_circle_after_first_click():
    canvas = make_canvas()
    tool = ArcTool(canvas)
    tool.mouse_press(FakeMouseEvent(0, 0))
    tool.mouse_move(FakeMouseEvent(2, 0))
    assert len(canvas.previews) >= 1
    preview = canvas.previews[-1]
    assert isinstance(preview, Arc)
    assert math.isclose(preview.radius, 2.0)


def test_arc_tool_preview_arc_after_second_click():
    canvas = make_canvas()
    tool = ArcTool(canvas)
    tool.mouse_press(FakeMouseEvent(0, 0))  # centro
    tool.mouse_press(FakeMouseEvent(1, 0))  # inicio
    tool.mouse_move(FakeMouseEvent(0, 1))   # fin candidato
    preview = canvas.previews[-1]
    assert isinstance(preview, Arc)
    assert math.isclose(preview.radius, 1.0)
    assert math.isclose(preview.start_angle, 0.0)
    assert math.isclose(preview.end_angle, math.pi / 2)
'''

# =========================================================================== #
# COMMIT 18 - Preview en SplineTool
# =========================================================================== #

TOOLS_SPLINE_PY = '''"""Herramienta interactiva para dibujar splines."""

from __future__ import annotations

from PyQt5.QtCore import Qt

from meshcad.core.geometry.spline import Spline
from meshcad.gui.tools.base import BaseTool


class SplineTool(BaseTool):
    """N clics para anadir puntos. Clic derecho para terminar.

    Muestra la spline en tiempo real a medida que se anaden puntos y
    se mueve el raton.
    """

    def mouse_press(self, event) -> None:
        if event.button() == Qt.RightButton:
            if len(self.points) >= 2:
                self.canvas.add_geometry(Spline(tuple(self.points)))
            self.points = []
            self.canvas.clear_preview()
            return

        p = self._scene_point(event)
        self.points.append(p)
        self._refresh_preview(event)

    def _refresh_preview(self, event) -> None:
        if not self.points:
            self.canvas.clear_preview()
            return
        p = self._scene_point(event)
        pts = tuple(self.points + [p])
        if len(pts) >= 2:
            self.canvas.show_preview(Spline(pts))
'''

TEST_SPLINE_TOOL = '''from meshcad.core.geometry.spline import Spline
from meshcad.gui.tools.spline_tool import SplineTool


class FakeCanvas:
    def __init__(self):
        self.geometries = []
        self.previews = []
        self.cleared = 0

    def add_geometry(self, geometry):
        self.geometries.append(geometry)

    def snap_to_vertex(self, p):
        return None

    def show_preview(self, geometry):
        self.previews.append(geometry)

    def clear_preview(self):
        self.cleared += 1


class FakeMouseEvent:
    def __init__(self, x, y, button=None):
        self._pos = (x, y)
        self._button = button

    def pos(self):
        from PyQt5.QtCore import QPoint

        return QPoint(self._pos[0], self._pos[1])

    def button(self):
        from PyQt5.QtCore import Qt

        return self._button if self._button is not None else Qt.LeftButton


def make_canvas():
    c = FakeCanvas()
    c.mapToScene = lambda qpoint: qpoint  # type: ignore[attr-defined]
    return c


def test_spline_tool_creates_spline_after_right_click():
    from PyQt5.QtCore import Qt

    canvas = make_canvas()
    tool = SplineTool(canvas)
    tool.mouse_press(FakeMouseEvent(0, 0))
    tool.mouse_press(FakeMouseEvent(1, 1))
    tool.mouse_press(FakeMouseEvent(2, 0))
    assert len(canvas.geometries) == 0
    tool.mouse_press(FakeMouseEvent(0, 0, button=Qt.RightButton))
    assert len(canvas.geometries) == 1
    assert isinstance(canvas.geometries[0], Spline)


def test_spline_needs_two_points():
    from PyQt5.QtCore import Qt

    canvas = make_canvas()
    tool = SplineTool(canvas)
    tool.mouse_press(FakeMouseEvent(0, 0))
    tool.mouse_press(FakeMouseEvent(0, 0, button=Qt.RightButton))
    assert len(canvas.geometries) == 0


def test_spline_preview_grows_with_mouse():
    canvas = make_canvas()
    tool = SplineTool(canvas)
    tool.mouse_press(FakeMouseEvent(0, 0))
    tool.mouse_move(FakeMouseEvent(1, 1))
    assert len(canvas.previews) >= 1
    preview = canvas.previews[-1]
    assert isinstance(preview, Spline)
    assert len(preview.points) == 2
'''


# =========================================================================== #
# Ejecucion
# =========================================================================== #

def main():
    check()

    commit(
        "Commit 16: Infraestructura de preview",
        {
            "src/meshcad/gui/items.py": ITEMS_PY,
            "src/meshcad/gui/canvas.py": CANVAS_PY,
            "src/meshcad/gui/tools/base.py": TOOLS_BASE_PY,
        },
        "feat(gui): infraestructura de vista previa en canvas",
    )

    commit(
        "Commit 17: Preview en linea y arco",
        {
            "src/meshcad/gui/tools/line_tool.py": TOOLS_LINE_PY,
            "src/meshcad/gui/tools/arc_tool.py": TOOLS_ARC_PY,
            "tests/gui/test_line_tool.py": TEST_LINE_TOOL,
            "tests/gui/test_arc_tool.py": TEST_ARC_TOOL,
        },
        "feat(gui): vista previa en tiempo real de linea y arco",
    )

    commit(
        "Commit 18: Preview en spline",
        {
            "src/meshcad/gui/tools/spline_tool.py": TOOLS_SPLINE_PY,
            "tests/gui/test_spline_tool.py": TEST_SPLINE_TOOL,
        },
        "feat(gui): vista previa en tiempo real de spline",
    )

    print()
    print("== Verificando todos los tests ==")
    run([sys.executable, "-m", "pytest", "-q"])

    print()
    print("== Historial ==")
    run(["git", "log", "--oneline", "--decorate"])

    print()
    print("Vista previa anadida. Ejecuta 'python -m meshcad'.")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print()
        print("ERROR:", e)
        sys.exit(1)