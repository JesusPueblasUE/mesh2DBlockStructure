from PyQt5.QtGui import QPainterPath
from PyQt5.QtWidgets import QGraphicsPathItem

from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.mesh.distribution import UniformDistribution
from meshcad.core.mesh.model import EdgeMeshSpec
from meshcad.core.topology.block import Block
from meshcad.core.topology.loop import Loop
from meshcad.gui.canvas import CadCanvas
from meshcad.gui.document import Document


def build_square(doc, n_nodes=4):
    t = doc.topology
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    v2 = t.add_vertex(Point2D(1, 1))
    v3 = t.add_vertex(Point2D(0, 1))
    e0 = t.add_edge(v0, v1, Line(v0.point, v1.point))
    e1 = t.add_edge(v1, v2, Line(v1.point, v2.point))
    e2 = t.add_edge(v2, v3, Line(v2.point, v3.point))
    e3 = t.add_edge(v3, v0, Line(v3.point, v0.point))
    loop = Loop()
    for e in (e0, e1, e2, e3):
        loop.add_edge(e.id)
    sides = loop.split_at_corners(t, [v0.id, v1.id, v2.id, v3.id])
    doc.add_block(Block(doc.next_block_id(), sides))
    for e in (e0, e1, e2, e3):
        doc.set_edge_spec(EdgeMeshSpec(e.id, n_nodes, UniformDistribution()))


def test_canvas_draws_mesh(qtbot):
    doc = Document()
    canvas = CadCanvas(doc)
    qtbot.addWidget(canvas)
    build_square(doc, n_nodes=4)

    assert canvas._mesh_item is None
    doc.generate_mesh()
    assert canvas._mesh_item is not None
    assert isinstance(canvas._mesh_item, QGraphicsPathItem)


def test_canvas_clear_mesh(qtbot):
    doc = Document()
    canvas = CadCanvas(doc)
    qtbot.addWidget(canvas)
    build_square(doc, n_nodes=4)
    doc.generate_mesh()
    assert canvas._mesh_item is not None
    canvas.clear_mesh()
    assert canvas._mesh_item is None
