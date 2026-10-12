import pytest

from meshcad.core.topology.block import Block
from meshcad.core.topology.block_side import BlockSide
from meshcad.core.topology.edge import OrientedEdge


def make_sides(n0=0, n1=0, n2=0, n3=0):
    return (
        BlockSide((OrientedEdge(0),), node_count=n0),
        BlockSide((OrientedEdge(1),), node_count=n1),
        BlockSide((OrientedEdge(2),), node_count=n2),
        BlockSide((OrientedEdge(3),), node_count=n3),
    )


def test_create():
    b = Block(0, make_sides())
    assert b.id == 0
    assert len(b.sides) == 4


def test_validate_defaults_pass():
    b = Block(0, make_sides())
    b.validate_opposite_sides()


def test_validate_matching_counts_pass():
    b = Block(0, make_sides(5, 7, 5, 7))
    b.validate_opposite_sides()


def test_validate_mismatch_0_2_raises():
    b = Block(0, make_sides(5, 7, 6, 7))
    with pytest.raises(ValueError):
        b.validate_opposite_sides()


def test_validate_mismatch_1_3_raises():
    b = Block(0, make_sides(5, 7, 5, 8))
    with pytest.raises(ValueError):
        b.validate_opposite_sides()
