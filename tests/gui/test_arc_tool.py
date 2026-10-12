import math

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
