"""Modelo de malla: distribuciones por arista y consultas por lado."""

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
    """Especificacion de malla de una arista.

    n_nodes es el numero total de nodos, incluyendo ambos extremos.
    distribution define como se reparten en el parametro t en [0, 1].
    """

    edge_id: int
    n_nodes: int
    distribution: NodeDistribution

    def __post_init__(self):
        if self.n_nodes < 2:
            raise ValueError("n_nodes debe ser >= 2")


class MeshModel:
    """Distribuciones de nodos asociadas a las aristas.

    Una misma arista puede pertenecer a varios bloques; la distribucion
    se guarda una sola vez y todos los bloques la comparten.
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
        """Numero de nodos de un lado concatenando sus aristas.

        Si el lado tiene k aristas con n_0, ..., n_{k-1} nodos cada una,
        el total es sum(n_i) - (k - 1), porque los extremos de aristas
        consecutivas se solapan en un vertice.
        """
        if not side.oriented_edges:
            return 0
        total = 0
        for i, oe in enumerate(side.oriented_edges):
            spec = self.get_spec(oe.edge_id)
            total += spec.n_nodes if i == 0 else spec.n_nodes - 1
        return total

    def side_samples(self, side: BlockSide, topology: Topology) -> List[Point2D]:
        """Puntos a lo largo de un lado, en el orden de recorrido."""
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
