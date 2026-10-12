"""Items graficos que representan entidades geometricas en la escena."""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainterPath, QPen
from PyQt5.QtWidgets import QGraphicsPathItem

from meshcad.core.geometry.entity import GeometryEntity

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
    """Item QGraphics que dibuja una entidad geometrica.

    En modo preview la pluma es discontinua y clara, no es seleccionable
    y tiene un z-value menor para que quede por debajo de la geometria real.
    """

    def __init__(self, geometry: GeometryEntity, preview: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.geometry = geometry
        self.setPath(_build_path(geometry))

        if preview:
            pen = QPen(QColor(90, 150, 220))
            pen.setWidthF(1.5)
            pen.setCosmetic(True)
            pen.setStyle(Qt.DashLine)
            self.setZValue(5.0)
        else:
            pen = QPen(QColor(30, 90, 200))
            pen.setWidthF(2.0)
            pen.setCosmetic(True)
            self.setFlag(QGraphicsPathItem.ItemIsSelectable, True)
            self.setZValue(0.0)

        self.setPen(pen)
