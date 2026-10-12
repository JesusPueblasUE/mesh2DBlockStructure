from meshcad.core.geometry.line import Line
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
