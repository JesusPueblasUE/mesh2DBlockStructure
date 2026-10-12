"""Serializacion JSON de geometria, topologia, malla y bloques."""

from __future__ import annotations

from typing import Any, Dict, List

from meshcad.core.geometry.arc import Arc
from meshcad.core.geometry.entity import GeometryEntity
from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.geometry.spline import Spline
from meshcad.core.mesh.distribution import (
    BiasedDistribution,
    NodeDistribution,
    UniformDistribution,
)


# ------------------------------- helpers ------------------------------- #


def _point_to_list(p: Point2D) -> List[float]:
    return [p.x, p.y]


def _point_from_list(data) -> Point2D:
    return Point2D(float(data[0]), float(data[1]))


# ------------------------------ geometria ------------------------------ #


def geometry_to_dict(g: GeometryEntity) -> Dict[str, Any]:
    if isinstance(g, Line):
        return {
            "type": "line",
            "start": _point_to_list(g.start),
            "end": _point_to_list(g.end),
        }
    if isinstance(g, Arc):
        return {
            "type": "arc",
            "center": _point_to_list(g.center),
            "radius": g.radius,
            "start_angle": g.start_angle,
            "end_angle": g.end_angle,
        }
    if isinstance(g, Spline):
        return {
            "type": "spline",
            "points": [_point_to_list(p) for p in g.points],
        }
    raise TypeError("Tipo de geometria no serializable: {}".format(type(g).__name__))


def geometry_from_dict(data: Dict[str, Any]) -> GeometryEntity:
    t = data.get("type")
    if t == "line":
        return Line(_point_from_list(data["start"]), _point_from_list(data["end"]))
    if t == "arc":
        return Arc(
            _point_from_list(data["center"]),
            float(data["radius"]),
            float(data["start_angle"]),
            float(data["end_angle"]),
        )
    if t == "spline":
        pts = tuple(_point_from_list(p) for p in data["points"])
        return Spline(pts)
    raise ValueError("Tipo de geometria desconocido: {!r}".format(t))


# --------------------------- distribuciones ---------------------------- #


def distribution_to_dict(d: NodeDistribution) -> Dict[str, Any]:
    if isinstance(d, UniformDistribution):
        return {"type": "uniform"}
    if isinstance(d, BiasedDistribution):
        return {
            "type": "biased",
            "bias": d.bias,
            "from_start": d.from_start,
        }
    raise TypeError("Distribucion no serializable: {}".format(type(d).__name__))


def distribution_from_dict(data: Dict[str, Any]) -> NodeDistribution:
    t = data.get("type")
    if t == "uniform":
        return UniformDistribution()
    if t == "biased":
        return BiasedDistribution(
            bias=float(data["bias"]),
            from_start=bool(data.get("from_start", True)),
        )
    raise ValueError("Distribucion desconocida: {!r}".format(t))
