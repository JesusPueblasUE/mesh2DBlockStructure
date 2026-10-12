import math

import pytest

from meshcad.core.geometry.arc import Arc
from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.mesh.distribution import BiasedDistribution, UniformDistribution
from meshcad.core.mesh.model import EdgeMeshSpec
from meshcad.core.topology.block import Block
from meshcad.core.topology.block_side import BlockSide
from meshcad.core.topology.edge import OrientedEdge
from meshcad.core.topology.loop import Loop
from meshcad.core.topology.topology import Topology
from meshcad.io.json_io import (
    block_from_dict,
    block_to_dict,
    edge_spec_from_dict,
    edge_spec_to_dict,
    topology_from_dict,
    topology_to_dict,
)


def make_square_topology():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    v2 = t.add_vertex(Point2D(1, 1))
    v3 = t.add_vertex(Point2D(0, 1))
    t.add_edge(v0, v1, Line(v0.point, v1.point))
    t.add_edge(v1, v2, Line(v1.point, v2.point))
    t.add_edge(v2, v3, Arc(Point2D(0.5, 0.5), 0.5, math.pi / 2, math.pi))
    t.add_edge(v3, v0, Line(v3.point, v0.point))
    return t


def test_topology_round_trip_preserves_ids():
    t = make_square_topology()
    data = topology_to_dict(t)
    back = topology_from_dict(data)
    assert sorted(v.id for v in back.vertices()) == sorted(
        v.id for v in t.vertices()
    )
    assert sorted(e.id for e in back.edges()) == sorted(e.id for e in t.edges())


def test_topology_round_trip_preserves_geometry():
    t = make_square_topology()
    back = topology_from_dict(topology_to_dict(t))
    for e in t.edges():
        be = back.get_edge(e.id)
        assert isinstance(be.geometry, type(e.geometry))
        assert be.start_vertex_id == e.start_vertex_id
        assert be.end_vertex_id == e.end_vertex_id


def test_topology_counter_continues_after_load():
    t = make_square_topology()
    back = topology_from_dict(topology_to_dict(t))
    v_new = back.add_vertex(Point2D(10, 10))
    v_last_id = max(v.id for v in t.vertices())
    assert v_new.id == v_last_id + 1


def test_edge_spec_round_trip():
    spec = EdgeMeshSpec(3, 7, BiasedDistribution(bias=1.5))
    data = edge_spec_to_dict(spec)
    back = edge_spec_from_dict(data)
    assert back.edge_id == 3
    assert back.n_nodes == 7
    assert isinstance(back.distribution, BiasedDistribution)
    assert math.isclose(back.distribution.bias, 1.5)


def test_block_round_trip():
    sides = (
        BlockSide((OrientedEdge(0),), node_count=4),
        BlockSide((OrientedEdge(1, reversed=True),), node_count=5),
        BlockSide((OrientedEdge(2),), node_count=4),
        BlockSide((OrientedEdge(3, reversed=True),), node_count=5),
    )
    block = Block(7, sides)
    data = block_to_dict(block)
    back = block_from_dict(data)
    assert back.id == 7
    assert back.sides[0].edge_ids() == [0]
    assert back.sides[1].oriented_edges[0].reversed is True
    assert back.sides[2].node_count == 4
    back.validate_opposite_sides()


def test_block_from_dict_rejects_wrong_sides():
    with pytest.raises(ValueError):
        block_from_dict({"id": 0, "sides": []})
