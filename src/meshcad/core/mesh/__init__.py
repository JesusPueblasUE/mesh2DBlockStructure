"""Generacion de malla estructurada y distribuciones de nodos."""

from meshcad.core.mesh.distribution import (
    BiasedDistribution,
    NodeDistribution,
    UniformDistribution,
)
from meshcad.core.mesh.model import EdgeMeshSpec, MeshModel, DEFAULT_N_NODES
from meshcad.core.mesh.tfi import tfi_grid

__all__ = [
    "NodeDistribution",
    "UniformDistribution",
    "BiasedDistribution",
    "EdgeMeshSpec",
    "MeshModel",
    "DEFAULT_N_NODES",
    "tfi_grid",
]
