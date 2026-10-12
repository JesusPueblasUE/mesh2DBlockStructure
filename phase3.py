#!/usr/bin/env python3
"""
Fase 3 del proyecto MeshCAD: GUI CAD basica.

Crea los commits atomicos de la fase 3:
Document, CadCanvas, herramientas de linea/arco/spline,
snapping y visualizacion.

Uso:
    cd meshcad
    python phase3.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()


def check():
    if not (ROOT / "pyproject.toml").exists():
        print("ERROR: ejecuta este script desde la raiz del proyecto meshcad.")
        sys.exit(1)
    if not (ROOT / ".git").exists():
        print("ERROR: este directorio no es un repositorio git.")
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
# COMMIT 11 - Document + CadCanvas
# =========================================================================== #

DOCUMENT_PY = '''"""Documento: contiene la topologia y el historial de undo/redo."""

from __future__ import annotations

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QUndoStack

from meshcad.core.topology.topology import Topology


class Document(QObject):
    """Estado del proyecto: topologia y pila de undo/redo."""

    topology_changed = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.topology = Topology()
        self.undo_stack = QUndoStack()

    def notify_change(self) -> None:
        self.topology_changed.emit()
'''

ITEMS_PY = '''"""Items graficos que representan entidades geometricas en la escena."""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainterPath, QPen
from PyQt5.QtWidgets import QGraphicsPathItem

from meshcad.core.geometry.arc import Arc
from meshcad.core.geometry.entity import GeometryEntity
from meshcad.core.geometry.line import Line
from meshcad.core.geometry.spline import Spline

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
    """Item QGraphics que dibuja una entidad geometrica."""

    def __init__(self, geometry: GeometryEntity, parent=None) -> None:
        super().__init__(parent)
        self.geometry = geometry
        self.setPath(_build_path(geometry))
        pen = QPen(QColor(30, 90, 200))
        pen.setWidthF(2.0)
        pen.setCosmetic(True)
        self.setPen(pen)
        self.setFlag(QGraphicsPathItem.ItemIsSelectable, True)
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

    Delega los eventos de raton en la herramienta activa (si la hay).
    """

    def __init__(self, document: Document, parent=None) -> None:
        super().__init__(parent)
        self.document = document
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setMouseTracking(True)
        self.setBackgroundBrush(QBrush(QColor(250, 250, 252)))

        # Herramienta activa (None = modo seleccion)
        self.tool = None
        # Cache de items de vertices por vertex_id
        self._vertex_items = {}

        self.document.topology_changed.connect(self._redraw_vertices)

    # ----------------------------- API publica --------------------------- #

    def set_tool(self, tool) -> None:
        if self.tool is not None:
            self.tool.cancel()
        self.tool = tool

    def add_geometry(self, geometry) -> None:
        """Registra la geometria en la topologia y la dibuja."""
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
        """Devuelve el vertice mas cercano dentro de la tolerancia, o None."""
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

        # Convertir tolerancia de pixeles a unidades de escena
        scale = self.transform().m11()
        if scale <= 0:
            return best
        tol_scene = SNAP_TOLERANCE / scale
        if best_dist is not None and best_dist <= tol_scene:
            return best
        return None

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
        # Eliminar items antiguos
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

MAIN_WINDOW_PY = '''"""Ventana principal de MeshCAD."""

import sys

from PyQt5.QtWidgets import QAction, QApplication, QMainWindow, QToolBar

from meshcad.gui.canvas import CadCanvas
from meshcad.gui.document import Document


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MeshCAD")
        self.resize(1024, 768)

        self.document = Document()
        self.canvas = CadCanvas(self.document)
        self.setCentralWidget(self.canvas)

        self._create_toolbar()

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("Herramientas", self)
        self.addToolBar(toolbar)

        self.action_select = QAction("Seleccionar", self)
        self.action_select.triggered.connect(lambda: self.canvas.set_tool(None))
        toolbar.addAction(self.action_select)


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
'''

TEST_DOCUMENT = '''from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.gui.document import Document


def test_document_starts_empty():
    doc = Document()
    assert len(doc.topology.vertices()) == 0
    assert len(doc.topology.edges()) == 0


def test_document_topology_changed_signal(qtbot):
    doc = Document()
    with qtbot.waitSignal(doc.topology_changed, timeout=1000):
        doc.notify_change()
'''


# =========================================================================== #
# COMMIT 12 - Line tool
# =========================================================================== #

TOOLS_INIT = '''"""Herramientas interactivas del CAD."""

from meshcad.gui.tools.base import BaseTool
from meshcad.gui.tools.line_tool import LineTool

__all__ = ["BaseTool", "LineTool"]
'''

TOOLS_BASE_PY = '''"""Clase base de las herramientas interactivas."""

from __future__ import annotations

from typing import List

from meshcad.core.geometry.point import Point2D


class BaseTool:
    """Interfaz comun a todas las herramientas interactivas.

    La herramienta recibe los eventos de raton del canvas. Acumula
    puntos hasta tener suficientes y luego llama a canvas.add_geometry.
    """

    def __init__(self, canvas) -> None:
        self.canvas = canvas
        self.points: List[Point2D] = []

    def mouse_press(self, event) -> None:  # pragma: no cover - abstracto
        raise NotImplementedError

    def mouse_move(self, event) -> None:
        return None

    def cancel(self) -> None:
        self.points = []

    def _scene_point(self, event) -> Point2D:
        pos = self.canvas.mapToScene(event.pos())
        p = Point2D(pos.x(), pos.y())
        snapped = self.canvas.snap_to_vertex(p)
        if snapped is not None:
            return snapped.point
        return p
'''

TOOLS_LINE_PY = '''"""Herramienta interactiva para dibujar segmentos de recta."""

from __future__ import annotations

from meshcad.core.geometry.line import Line
from meshcad.gui.tools.base import BaseTool


class LineTool(BaseTool):
    """Dos clics: inicio y fin."""

    def mouse_press(self, event) -> None:
        p = self._scene_point(event)
        self.points.append(p)

        if len(self.points) == 2:
            self.canvas.add_geometry(Line(self.points[0], self.points[1]))
            self.points = []
'''

MAIN_WINDOW_WITH_LINE = '''"""Ventana principal de MeshCAD."""

import sys

from PyQt5.QtWidgets import QAction, QApplication, QMainWindow, QToolBar

from meshcad.gui.canvas import CadCanvas
from meshcad.gui.document import Document
from meshcad.gui.tools.line_tool import LineTool


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MeshCAD")
        self.resize(1024, 768)

        self.document = Document()
        self.canvas = CadCanvas(self.document)
        self.setCentralWidget(self.canvas)

        self._create_toolbar()

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


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
'''

TEST_LINE_TOOL = '''from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.gui.document import Document
from meshcad.gui.tools.line_tool import LineTool


class FakeCanvas:
    def __init__(self, document):
        self.document = document
        self.geometries = []

    def add_geometry(self, geometry):
        self.geometries.append(geometry)
        return geometry

    def snap_to_vertex(self, p):
        return None


class FakeMouseEvent:
    def __init__(self, x, y):
        self._pos = (x, y)

    def pos(self):
        from PyQt5.QtCore import QPoint

        return QPoint(self._pos[0], self._pos[1])


def test_line_tool_creates_line_after_two_clicks():
    canvas = FakeCanvas(Document())
    # Sobrescribimos mapToScene para el canvas fake
    canvas.mapToScene = lambda qpoint: qpoint  # type: ignore[attr-defined]
    canvas.snap_to_vertex = lambda p: None  # type: ignore[attr-defined]

    tool = LineTool(canvas)
    tool.mouse_press(FakeMouseEvent(0, 0))
    assert len(tool.points) == 1
    tool.mouse_press(FakeMouseEvent(10, 5))
    assert len(tool.points) == 0
    assert len(canvas.geometries) == 1
    geom = canvas.geometries[0]
    assert isinstance(geom, Line)
    assert geom.start == Point2D(0, 0)
    assert geom.end == Point2D(10, 5)
'''


# =========================================================================== #
# COMMIT 13 - Arc tool
# =========================================================================== #

TOOLS_ARC_PY = '''"""Herramienta interactiva para dibujar arcos de circulo."""

from __future__ import annotations

import math

from meshcad.core.geometry.arc import Arc
from meshcad.gui.tools.base import BaseTool


class ArcTool(BaseTool):
    """Tres clics: centro, inicio, fin. El arco se recorre CCW."""

    def mouse_press(self, event) -> None:
        p = self._scene_point(event)
        self.points.append(p)

        if len(self.points) == 3:
            center, start, end = self.points
            radius = center.distance_to(start)
            if radius > 1e-9:
                a0 = math.atan2(start.y - center.y, start.x - center.x)
                a1 = math.atan2(end.y - center.y, end.x - center.x)
                self.canvas.add_geometry(Arc(center, radius, a0, a1))
            self.points = []
'''

TOOLS_INIT_ARC = '''"""Herramientas interactivas del CAD."""

from meshcad.gui.tools.base import BaseTool
from meshcad.gui.tools.line_tool import LineTool
from meshcad.gui.tools.arc_tool import ArcTool

__all__ = ["BaseTool", "LineTool", "ArcTool"]
'''

MAIN_WINDOW_WITH_ARC = '''"""Ventana principal de MeshCAD."""

import sys

from PyQt5.QtWidgets import QAction, QApplication, QMainWindow, QToolBar

from meshcad.gui.canvas import CadCanvas
from meshcad.gui.document import Document
from meshcad.gui.tools.arc_tool import ArcTool
from meshcad.gui.tools.line_tool import LineTool


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MeshCAD")
        self.resize(1024, 768)

        self.document = Document()
        self.canvas = CadCanvas(self.document)
        self.setCentralWidget(self.canvas)

        self._create_toolbar()

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


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
'''

TEST_ARC_TOOL = '''import math

from meshcad.core.geometry.arc import Arc
from meshcad.core.geometry.point import Point2D
from meshcad.gui.document import Document
from meshcad.gui.tools.arc_tool import ArcTool


class FakeCanvas:
    def __init__(self):
        self.geometries = []

    def add_geometry(self, geometry):
        self.geometries.append(geometry)

    def snap_to_vertex(self, p):
        return None


class FakeMouseEvent:
    def __init__(self, x, y):
        self._pos = (x, y)

    def pos(self):
        from PyQt5.QtCore import QPoint

        return QPoint(self._pos[0], self._pos[1])


def test_arc_tool_creates_arc_after_three_clicks():
    canvas = FakeCanvas()
    canvas.mapToScene = lambda qpoint: qpoint  # type: ignore[attr-defined]

    tool = ArcTool(canvas)
    tool.mouse_press(FakeMouseEvent(0, 0))   # centro
    tool.mouse_press(FakeMouseEvent(1, 0))   # inicio
    tool.mouse_press(FakeMouseEvent(0, 1))   # fin
    assert len(canvas.geometries) == 1
    arc = canvas.geometries[0]
    assert isinstance(arc, Arc)
    assert math.isclose(arc.radius, 1.0)
    assert math.isclose(arc.start_angle, 0.0)
    assert math.isclose(arc.end_angle, math.pi / 2)
'''


# =========================================================================== #
# COMMIT 14 - Spline tool
# =========================================================================== #

TOOLS_SPLINE_PY = '''"""Herramienta interactiva para dibujar splines."""

from __future__ import annotations

from PyQt5.QtCore import Qt

from meshcad.core.geometry.spline import Spline
from meshcad.gui.tools.base import BaseTool


class SplineTool(BaseTool):
    """N clics para anadir puntos. Clic derecho para terminar."""

    def mouse_press(self, event) -> None:
        if event.button() == Qt.RightButton:
            if len(self.points) >= 2:
                self.canvas.add_geometry(Spline(tuple(self.points)))
            self.points = []
            return

        p = self._scene_point(event)
        self.points.append(p)
'''

TOOLS_INIT_SPLINE = '''"""Herramientas interactivas del CAD."""

from meshcad.gui.tools.base import BaseTool
from meshcad.gui.tools.line_tool import LineTool
from meshcad.gui.tools.arc_tool import ArcTool
from meshcad.gui.tools.spline_tool import SplineTool

__all__ = ["BaseTool", "LineTool", "ArcTool", "SplineTool"]
'''

MAIN_WINDOW_WITH_SPLINE = '''"""Ventana principal de MeshCAD."""

import sys

from PyQt5.QtWidgets import QAction, QApplication, QMainWindow, QToolBar

from meshcad.gui.canvas import CadCanvas
from meshcad.gui.document import Document
from meshcad.gui.tools.arc_tool import ArcTool
from meshcad.gui.tools.line_tool import LineTool
from meshcad.gui.tools.spline_tool import SplineTool


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MeshCAD")
        self.resize(1024, 768)

        self.document = Document()
        self.canvas = CadCanvas(self.document)
        self.setCentralWidget(self.canvas)

        self._create_toolbar()

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


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
'''

TEST_SPLINE_TOOL = '''from meshcad.core.geometry.spline import Spline
from meshcad.gui.tools.spline_tool import SplineTool


class FakeCanvas:
    def __init__(self):
        self.geometries = []

    def add_geometry(self, geometry):
        self.geometries.append(geometry)

    def snap_to_vertex(self, p):
        return None


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


def test_spline_tool_creates_spline_after_right_click():
    from PyQt5.QtCore import Qt

    canvas = FakeCanvas()
    canvas.mapToScene = lambda qpoint: qpoint  # type: ignore[attr-defined]

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

    canvas = FakeCanvas()
    canvas.mapToScene = lambda qpoint: qpoint  # type: ignore[attr-defined]

    tool = SplineTool(canvas)
    tool.mouse_press(FakeMouseEvent(0, 0))
    tool.mouse_press(FakeMouseEvent(0, 0, button=Qt.RightButton))
    assert len(canvas.geometries) == 0
'''


# =========================================================================== #
# COMMIT 15 - Snapping test + integration
# =========================================================================== #

TEST_CANVAS_SNAPPING = '''import math

from meshcad.core.geometry.point import Point2D
from meshcad.gui.document import Document


def test_snap_to_vertex(qtbot):
    """El canvas debe encontrar el vertice mas cercano dentro de tolerancia."""
    from meshcad.gui.canvas import CadCanvas

    doc = Document()
    canvas = CadCanvas(doc)
    qtbot.addWidget(canvas)

    v = doc.topology.add_vertex(Point2D(0.0, 0.0))

    # Con tolerancia por defecto, un punto cercano debe hacer snap
    near = Point2D(0.5, 0.5)
    snapped = canvas.snap_to_vertex(near)
    assert snapped is v


def test_snap_to_vertex_far(qtbot):
    from meshcad.gui.canvas import CadCanvas

    doc = Document()
    canvas = CadCanvas(doc)
    qtbot.addWidget(canvas)

    doc.topology.add_vertex(Point2D(0.0, 0.0))
    far = Point2D(100.0, 100.0)
    assert canvas.snap_to_vertex(far) is None
'''


# =========================================================================== #
# Ejecucion
# =========================================================================== #

def main():
    check()

    commit(
        "Commit 11/15: Document + CadCanvas",
        {
            "src/meshcad/gui/document.py": DOCUMENT_PY,
            "src/meshcad/gui/items.py": ITEMS_PY,
            "src/meshcad/gui/canvas.py": CANVAS_PY,
            "src/meshcad/gui/main_window.py": MAIN_WINDOW_PY,
            "tests/gui/__init__.py": "",
            "tests/gui/test_document.py": TEST_DOCUMENT,
        },
        "feat(gui): documento y lienzo QGraphicsView",
    )

    commit(
        "Commit 12/15: Line tool",
        {
            "src/meshcad/gui/tools/__init__.py": TOOLS_INIT,
            "src/meshcad/gui/tools/base.py": TOOLS_BASE_PY,
            "src/meshcad/gui/tools/line_tool.py": TOOLS_LINE_PY,
            "src/meshcad/gui/main_window.py": MAIN_WINDOW_WITH_LINE,
            "tests/gui/test_line_tool.py": TEST_LINE_TOOL,
        },
        "feat(gui): herramienta interactiva de linea",
    )

    commit(
        "Commit 13/15: Arc tool",
        {
            "src/meshcad/gui/tools/arc_tool.py": TOOLS_ARC_PY,
            "src/meshcad/gui/tools/__init__.py": TOOLS_INIT_ARC,
            "src/meshcad/gui/main_window.py": MAIN_WINDOW_WITH_ARC,
            "tests/gui/test_arc_tool.py": TEST_ARC_TOOL,
        },
        "feat(gui): herramienta interactiva de arco",
    )

    commit(
        "Commit 14/15: Spline tool",
        {
            "src/meshcad/gui/tools/spline_tool.py": TOOLS_SPLINE_PY,
            "src/meshcad/gui/tools/__init__.py": TOOLS_INIT_SPLINE,
            "src/meshcad/gui/main_window.py": MAIN_WINDOW_WITH_SPLINE,
            "tests/gui/test_spline_tool.py": TEST_SPLINE_TOOL,
        },
        "feat(gui): herramienta interactiva de spline",
    )

    commit(
        "Commit 15/15: Snapping test",
        {
            "tests/gui/test_canvas_snapping.py": TEST_CANVAS_SNAPPING,
        },
        "feat(gui): snapping a vertices y visualizacion",
    )

    print()
    print("== Verificando todos los tests ==")
    run([sys.executable, "-m", "pytest", "-q"])

    print()
    print("== Historial ==")
    run(["git", "log", "--oneline", "--decorate"])

    print()
    print("Fase 3 completada. Ejecuta 'python -m meshcad' para ver la GUI.")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print()
        print("ERROR:", e)
        sys.exit(1)