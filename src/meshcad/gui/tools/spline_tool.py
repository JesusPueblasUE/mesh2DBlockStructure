"""Herramienta interactiva para dibujar splines."""

from __future__ import annotations

from PyQt5.QtCore import Qt

from meshcad.core.geometry.spline import Spline
from meshcad.gui.tools.base import BaseTool


class SplineTool(BaseTool):
    """N clics para anadir puntos. Clic derecho para terminar."""

    def mouse_press(self, event) -> None:
        if event.button() == Qt.RightButton:
            if len(self.points) >= 2:
                self.canvas.add_geometry(Spline(tuple(self.points)))
            self.points = []
            return

        p = self._scene_point(event)
        self.points.append(p)
