from meshcad.core.topology.block_side import BlockSide
from meshcad.core.topology.edge import OrientedEdge


def test_create_empty():
    side = BlockSide(oriented_edges=())
    assert len(side) == 0
    assert side.node_count == 0
    assert side.edge_ids() == []


def test_create_with_edges():
    side = BlockSide(
        oriented_edges=(OrientedEdge(0), OrientedEdge(1, reversed=True)),
        node_count=5,
    )
    assert len(side) == 2
    assert side.node_count == 5
    assert side.edge_ids() == [0, 1]


def test_node_count_default():
    side = BlockSide(oriented_edges=(OrientedEdge(0),))
    assert side.node_count == 0
