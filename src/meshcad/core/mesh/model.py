"""Mesh model: per-edge distributions and side queries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from meshcad.core.geometry.point import Point2D
from meshcad.core.mesh.distribution import (
    NodeDistribution,
    UniformDistribution,
)
from meshcad.core.topology.block_side import BlockSide
from meshcad.core.topology.topology import Topology

DEFAULT_N_NODES = 5


@dataclass
class EdgeMeshSpec:
    """Especificacion de mesh de a edge.

    n_nodes es el number total de nodes, incluyendo ambos extremos.
    distribution define como se reparten en el parametro t en [0, 1].
    """

    edge_id: int
    n_nodes: int
    distribution: NodeDistribution

    def __post_init__(self):
        if self.n_nodes < 2:
            raise ValueError("n_nodes must be >= 2")


class MeshModel:
    """Distributions de nodes asociadas a las edges.

    Una misma edge can pertenecer a varios blocks; la distribucion
    se guarda a sola vez y all los blocks la comparten.
    """

    def __init__(self) -> None:
        self.edge_specs: Dict[int, EdgeMeshSpec] = {}

    # ----------------------------- acceso ------------------------------- #

    def get_spec(self, edge_id: int) -> EdgeMeshSpec:
        spec = self.edge_specs.get(edge_id)
        if spec is None:
            return EdgeMeshSpec(edge_id, DEFAULT_N_NODES, UniformDistribution())
        return spec

    def set_spec(self, spec: EdgeMeshSpec) -> None:
        self.edge_specs[spec.edge_id] = spec

    def clear_spec(self, edge_id: int) -> None:
        self.edge_specs.pop(edge_id, None)

    # ----------------------------- consultas ---------------------------- #

    def side_node_count(self, side: BlockSide) -> int:
        """Number of nodes de un lado concatenando sus edges.

        Si el lado tiene k edges with n_0, ..., n_{k-1} nodes cada a,
        el total es sum(n_i) - (k - 1), porque los extremos de edges
        consecutivas se solapan en un vertex.
        """
        if not side.oriented_edges:
            return 0
        total = 0
        for i, oe in enumerate(side.oriented_edges):
            spec = self.get_spec(oe.edge_id)
            total += spec.n_nodes if i == 0 else spec.n_nodes - 1
        return total

    def side_samples(self, side: BlockSide, topology: Topology) -> List[Point2D]:
        """Points along a side in traversal order."""
        samples: List[Point2D] = []
        for i, oe in enumerate(side.oriented_edges):
            edge = topology.get_edge(oe.edge_id)
            spec = self.get_spec(oe.edge_id)
            pts = spec.distribution.sample(edge.geometry, spec.n_nodes)
            if oe.reversed:
                pts = list(reversed(pts))
            if i > 0:
                pts = pts[1:]
            samples.extend(pts)
        return samples
