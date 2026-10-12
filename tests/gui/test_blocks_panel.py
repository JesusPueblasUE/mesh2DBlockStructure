from meshcad.core.mesh.distribution import UniformDistribution
from meshcad.core.mesh.model import EdgeMeshSpec
from meshcad.core.topology.block import Block
from meshcad.core.topology.block_side import BlockSide
from meshcad.core.topology.edge import OrientedEdge
from meshcad.gui.document import Document


def test_blocks_panel_refresh_without_blocks(qtbot):
    from meshcad.gui.blocks_panel import BlocksPanel

    doc = Document()
    panel = BlocksPanel(doc)
    qtbot.addWidget(panel)
    assert "Sin bloques" in panel.status.text()


def test_blocks_panel_lists_ok_block(qtbot):
    from meshcad.gui.blocks_panel import BlocksPanel

    doc = Document()
    sides = tuple(BlockSide((OrientedEdge(i),)) for i in range(4))
    block = Block(0, sides)
    doc.blocks.append(block)
    doc.set_edge_spec(EdgeMeshSpec(0, 5, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(1, 7, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(2, 5, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(3, 7, UniformDistribution()))

    panel = BlocksPanel(doc)
    qtbot.addWidget(panel)
    assert "1 bloques: 1 OK" in panel.status.text()


def test_blocks_panel_detects_mismatch(qtbot):
    from meshcad.gui.blocks_panel import BlocksPanel

    doc = Document()
    sides = tuple(BlockSide((OrientedEdge(i),)) for i in range(4))
    block = Block(0, sides)
    doc.blocks.append(block)
    doc.set_edge_spec(EdgeMeshSpec(0, 5, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(1, 6, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(2, 8, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(3, 6, UniformDistribution()))

    panel = BlocksPanel(doc)
    qtbot.addWidget(panel)
    assert "0 OK" in panel.status.text()
    assert "1 con desajustes" in panel.status.text()
