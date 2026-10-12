"""Persistencia (JSON) y exportacion (VTK)."""

from meshcad.io.json_io import (
    block_from_dict,
    block_side_from_dict,
    block_side_to_dict,
    block_to_dict,
    distribution_from_dict,
    distribution_to_dict,
    edge_spec_from_dict,
    edge_spec_to_dict,
    geometry_from_dict,
    geometry_to_dict,
    topology_from_dict,
    topology_to_dict,
)

__all__ = [
    "geometry_to_dict",
    "geometry_from_dict",
    "distribution_to_dict",
    "distribution_from_dict",
    "topology_to_dict",
    "topology_from_dict",
    "edge_spec_to_dict",
    "edge_spec_from_dict",
    "block_side_to_dict",
    "block_side_from_dict",
    "block_to_dict",
    "block_from_dict",
]
