"""Persistencia (JSON) y exportacion (VTK)."""

from meshcad.io.json_io import (
    distribution_from_dict,
    distribution_to_dict,
    geometry_from_dict,
    geometry_to_dict,
)

__all__ = [
    "geometry_to_dict",
    "geometry_from_dict",
    "distribution_to_dict",
    "distribution_from_dict",
]
