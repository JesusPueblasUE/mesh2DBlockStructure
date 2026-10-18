"""Structured mesh generation and node distributions."""

from meshcad.core.mesh.distribution import (
    BiasedDistribution,
    NodeDistribution,
    UniformDistribution,
)
from meshcad.core.mesh.model import EdgeMeshSpec, MeshModel, DEFAULT_N_NODES
from meshcad.core.mesh.tfi import tfi_grid
from meshcad.core.mesh.generator import BlockMesh, mesh_block
from meshcad.core.mesh.smoothing import SmoothingOptions, improve_grid

__all__ = [
    "NodeDistribution",
    "UniformDistribution",
    "BiasedDistribution",
    "EdgeMeshSpec",
    "MeshModel",
    "DEFAULT_N_NODES",
    "tfi_grid",
    "BlockMesh",
    "mesh_block",
    "SmoothingOptions",
    "improve_grid",
]
