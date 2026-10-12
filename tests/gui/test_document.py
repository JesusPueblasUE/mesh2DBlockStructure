from meshcad.core.mesh.distribution import UniformDistribution
from meshcad.core.mesh.model import EdgeMeshSpec
from meshcad.core.topology.block import Block
from meshcad.core.topology.block_side import BlockSide
from meshcad.core.topology.edge import OrientedEdge
from meshcad.gui.document import Document


def test_document_starts_empty():
    doc = Document()
    assert len(doc.topology.vertices()) == 0
    assert len(doc.blocks) == 0
    assert len(doc.mesh.edge_specs) == 0


def test_set_edge_spec_emits_mesh_changed(qtbot):
    doc = Document()
    with qtbot.waitSignal(doc.mesh_changed, timeout=1000):
        doc.set_edge_spec(EdgeMeshSpec(0, 7, UniformDistribution()))
    assert doc.mesh.get_spec(0).n_nodes == 7


def test_recompute_blocks_updates_node_counts(qtbot):
    doc = Document()
    sides = tuple(BlockSide((OrientedEdge(i),)) for i in range(4))
    block = Block(0, sides)
    doc.blocks.append(block)

    doc.set_edge_spec(EdgeMeshSpec(0, 5, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(1, 7, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(2, 5, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(3, 7, UniformDistribution()))

    assert block.sides[0].node_count == 5
    assert block.sides[1].node_count == 7
    assert block.sides[2].node_count == 5
    assert block.sides[3].node_count == 7
    block.validate_opposite_sides()


def test_opposite_sides_mismatch_raises_after_recompute(qtbot):
    import pytest

    doc = Document()
    sides = tuple(BlockSide((OrientedEdge(i),)) for i in range(4))
    block = Block(0, sides)
    doc.blocks.append(block)

    doc.set_edge_spec(EdgeMeshSpec(0, 5, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(1, 6, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(2, 7, UniformDistribution()))  # desajuste
    doc.set_edge_spec(EdgeMeshSpec(3, 6, UniformDistribution()))

    with pytest.raises(ValueError):
        block.validate_opposite_sides()
