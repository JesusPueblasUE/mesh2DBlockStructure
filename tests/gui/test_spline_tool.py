from meshcad.core.geometry.spline import Spline
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
