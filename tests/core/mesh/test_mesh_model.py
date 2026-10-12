import math

import pytest

from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.mesh.distribution import (
    BiasedDistribution,
    UniformDistribution,
)
from meshcad.core.mesh.model import DEFAULT_N_NODES, EdgeMeshSpec, MeshModel
from meshcad.core.topology.block_side import BlockSide
from meshcad.core.topology.edge import OrientedEdge
from meshcad.core.topology.topology import Topology


def test_edge_spec_requires_two_nodes():
    with pytest.raises(ValueError):
        EdgeMeshSpec(0, 1, UniformDistribution())


def test_default_spec_is_uniform():
    m = MeshModel()
    spec = m.get_spec(42)
    assert spec.n_nodes == DEFAULT_N_NODES
    assert isinstance(spec.distribution, UniformDistribution)


def test_set_and_get_spec():
    m = MeshModel()
    spec = EdgeMeshSpec(3, 7, BiasedDistribution(bias=1.5))
    m.set_spec(spec)
    assert m.get_spec(3) is spec


def test_clear_spec_returns_default():
    m = MeshModel()
    m.set_spec(EdgeMeshSpec(0, 9, UniformDistribution()))
    m.clear_spec(0)
    assert m.get_spec(0).n_nodes == DEFAULT_N_NODES


def test_side_node_count_single_edge():
    m = MeshModel()
    m.set_spec(EdgeMeshSpec(0, 6, UniformDistribution()))
    side = BlockSide((OrientedEdge(0),))
    assert m.side_node_count(side) == 6


def test_side_node_count_two_edges_overlap():
    m = MeshModel()
    m.set_spec(EdgeMeshSpec(0, 5, UniformDistribution()))
    m.set_spec(EdgeMeshSpec(1, 4, UniformDistribution()))
    side = BlockSide((OrientedEdge(0), OrientedEdge(1)))
    # 5 + 4 - 1 = 8
    assert m.side_node_count(side) == 8


def test_side_node_count_defaults_used_when_unset():
    m = MeshModel()
    side = BlockSide((OrientedEdge(0),))
    assert m.side_node_count(side) == DEFAULT_N_NODES


def test_side_samples_single_edge():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(10, 0))
    e = t.add_edge(v0, v1, Line(v0.point, v1.point))

    m = MeshModel()
    m.set_spec(EdgeMeshSpec(e.id, 3, UniformDistribution()))

    side = BlockSide((OrientedEdge(e.id),))
    pts = m.side_samples(side, t)
    assert pts == [Point2D(0, 0), Point2D(5, 0), Point2D(10, 0)]


def test_side_samples_reversed_edge():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(10, 0))
    e = t.add_edge(v0, v1, Line(v0.point, v1.point))

    m = MeshModel()
    m.set_spec(EdgeMeshSpec(e.id, 3, UniformDistribution()))

    side = BlockSide((OrientedEdge(e.id, reversed=True),))
    pts = m.side_samples(side, t)
    assert pts == [Point2D(10, 0), Point2D(5, 0), Point2D(0, 0)]


def test_side_samples_two_edges_no_duplicate_joint():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(10, 0))
    v2 = t.add_vertex(Point2D(10, 10))
    e0 = t.add_edge(v0, v1, Line(v0.point, v1.point))
    e1 = t.add_edge(v1, v2, Line(v1.point, v2.point))

    m = MeshModel()
    m.set_spec(EdgeMeshSpec(e0.id, 3, UniformDistribution()))
    m.set_spec(EdgeMeshSpec(e1.id, 3, UniformDistribution()))

    side = BlockSide((OrientedEdge(e0.id), OrientedEdge(e1.id)))
    pts = m.side_samples(side, t)
    assert len(pts) == 5  # 3 + 3 - 1
    assert pts[0] == Point2D(0, 0)
    assert pts[2] == Point2D(10, 0)
    assert pts[-1] == Point2D(10, 10)
