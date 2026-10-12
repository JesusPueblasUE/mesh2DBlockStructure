"""Items graficos que representan entidades geometricas en la escena."""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainterPath, QPen
from PyQt5.QtWidgets import QGraphicsPathItem

from meshcad.core.geometry.arc import Arc
from meshcad.core.geometry.entity import GeometryEntity
from meshcad.core.geometry.line import Line
from meshcad.core.geometry.spline import Spline

SAMPLE_COUNT = 60


def _build_path(geometry: GeometryEntity) -> QPainterPath:
    path = QPainterPath()
    pts = geometry.sample(SAMPLE_COUNT)
    if not pts:
        return path
    path.moveTo(pts[0].x, pts[0].y)
    for p in pts[1:]:
        path.lineTo(p.x, p.y)
    return path


class GeometryItem(QGraphicsPathItem):
    """Item QGraphics que dibuja una entidad geometrica."""

    def __init__(self, geometry: GeometryEntity, parent=None) -> None:
        super().__init__(parent)
        self.geometry = geometry
        self.setPath(_build_path(geometry))
        pen = QPen(QColor(30, 90, 200))
        pen.setWidthF(2.0)
        pen.setCosmetic(True)
        self.setPen(pen)
        self.setFlag(QGraphicsPathItem.ItemIsSelectable, True)
