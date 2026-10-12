from meshcad.core.geometry.spline import Spline
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
