import math
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtTest import QTest
from meshcad.core.geometry.arc import Arc
from meshcad.core.geometry.point import Point2D
from meshcad.gui.canvas import CadCanvas
from meshcad.gui.document import Document


def make_arc_canvas(qtbot):
    doc = Document(); canvas = CadCanvas(doc); canvas.resize(700, 500)
    qtbot.addWidget(canvas); canvas.show(); qtbot.waitExposed(canvas)
    v0 = doc.topology.add_vertex(Point2D(-100.0, 0.0))
    v1 = doc.topology.add_vertex(Point2D(100.0, 0.0))
    edge = doc.topology.add_edge(v0, v1, Arc(Point2D(0.0, 0.0), 100.0, math.pi, 2.0 * math.pi))
    doc.notify_change(); canvas.centerOn(0.0, 0.0)
    return doc, canvas, edge


def test_grip_near_finds_arc_center(qtbot):
    doc, canvas, edge = make_arc_canvas(qtbot)
    hit = canvas._grip_near(Point2D(0.0, 0.0))
    assert hit is not None
    assert hit[0] == edge.id and hit[1] == 0 and hit[2] == Point2D(0.0, 0.0)


def test_double_click_arc_center_opens_editor_and_moves_center(qtbot, monkeypatch):
    doc, canvas, edge = make_arc_canvas(qtbot)
    monkeypatch.setattr(canvas, "_edit_point_dialog", lambda title, point: Point2D(0.0, 50.0))
    screen_point = canvas.mapFromScene(0.0, 0.0)
    QTest.mouseDClick(canvas.viewport(), Qt.LeftButton, pos=QPoint(screen_point.x(), screen_point.y()))
    arc = doc.topology.get_edge(edge.id).geometry
    assert arc.center == Point2D(0.0, 50.0)
    assert math.isclose(arc.radius, math.hypot(100.0, 50.0))
    assert arc.start_point().distance_to(Point2D(-100.0, 0.0)) < 1e-7
    assert arc.end_point().distance_to(Point2D(100.0, 0.0)) < 1e-7


def test_cancel_does_not_modify_arc(qtbot, monkeypatch):
    doc, canvas, edge = make_arc_canvas(qtbot)
    original = doc.topology.get_edge(edge.id).geometry
    monkeypatch.setattr(canvas, "_edit_point_dialog", lambda title, point: None)
    p = canvas.mapFromScene(0.0, 0.0)
    QTest.mouseDClick(canvas.viewport(), Qt.LeftButton, pos=p)
    assert doc.topology.get_edge(edge.id).geometry == original
