from meshcad.core.topology.block import Block
from meshcad.core.topology.block_side import BlockSide
from meshcad.core.topology.edge import OrientedEdge
from meshcad.gui.document import Document


def test_document_starts_empty():
    doc = Document()
    assert len(doc.topology.vertices()) == 0
    assert len(doc.blocks) == 0


def test_next_block_id_is_monotonic():
    doc = Document()
    assert doc.next_block_id() == 0
    assert doc.next_block_id() == 1
    assert doc.next_block_id() == 2


def test_add_block_emits_signal(qtbot):
    doc = Document()
    sides = tuple(
        BlockSide((OrientedEdge(i),)) for i in range(4)
    )
    block = Block(0, sides)
    with qtbot.waitSignal(doc.blocks_changed, timeout=1000):
        doc.add_block(block)
    assert len(doc.blocks) == 1
