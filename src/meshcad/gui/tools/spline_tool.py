"""Interactive tool for drawing splines."""

from __future__ import annotations

from PyQt5.QtCore import Qt

from meshcad.core.geometry.spline import Spline
from meshcad.gui.tools.base import BaseTool


class SplineTool(BaseTool):
    """N clics for anadir puntos. Clic derecho for terminar.

    Muestra la spline en tiempo real a medida que se anaden puntos y
    se mueve el raton.
    """

    def mouse_press(self, event) -> None:
        if event.button() == Qt.RightButton:
            if len(self.points) >= 2:
                self.canvas.add_geometry(Spline(tuple(self.points)))
            self.points = []
            self.canvas.clear_preview()
            return

        p = self._scene_point(event)
        self.points.append(p)
        self._refresh_preview(event)

    def _refresh_preview(self, event) -> None:
        if not self.points:
            self.canvas.clear_preview()
            return
        p = self._scene_point(event)
        pts = tuple(self.points + [p])
        if len(pts) >= 2:
            self.canvas.show_preview(Spline(pts))
