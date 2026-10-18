import math
from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.gui.canvas import CadCanvas
from meshcad.gui.document import Document


def make_canvas(qtbot):
    doc = Document(); canvas = CadCanvas(doc); canvas.resize(900, 600)
    qtbot.addWidget(canvas); canvas.show(); qtbot.waitExposed(canvas)
    v0 = doc.topology.add_vertex(Point2D(-900.0, -320.0))
    v1 = doc.topology.add_vertex(Point2D(120.0, 740.0))
    doc.topology.add_edge(v0, v1, Line(v0.point, v1.point)); doc.notify_change()
    return canvas, v0, v1


def test_reset_zoom_fits_complete_model(qtbot):
    canvas, v0, v1 = make_canvas(qtbot)
    canvas.scale(4.0, 4.0); canvas.centerOn(5000.0, -5000.0); canvas.reset_zoom()
    assert canvas.transform().m22() < 0.0
    viewport = canvas.viewport().rect().adjusted(-2, -2, 2, 2)
    for p in (v0.point, v1.point):
        assert viewport.contains(canvas.mapFromScene(p.x, p.y))


def test_reset_zoom_recenters_after_pan(qtbot):
    canvas, v0, v1 = make_canvas(qtbot); canvas.reset_zoom()
    center = canvas.mapToScene(canvas.viewport().rect().center())
    assert math.isclose(center.x(), (v0.point.x + v1.point.x) / 2, abs_tol=3.0)
    assert math.isclose(center.y(), (v0.point.y + v1.point.y) / 2, abs_tol=3.0)


def test_reset_zoom_empty_document(qtbot):
    canvas = CadCanvas(Document()); qtbot.addWidget(canvas); canvas.reset_zoom()
    assert canvas.transform().m11() == 1.0
    assert canvas.transform().m22() == -1.0
