"""Herramienta interactiva para dibujar arcos de circulo."""

from __future__ import annotations

import math

from meshcad.core.geometry.arc import Arc
from meshcad.gui.tools.base import BaseTool


class ArcTool(BaseTool):
    """Tres clics: centro, inicio, fin. El arco se recorre CCW."""

    def mouse_press(self, event) -> None:
        p = self._scene_point(event)
        self.points.append(p)

        if len(self.points) == 3:
            center, start, end = self.points
            radius = center.distance_to(start)
            if radius > 1e-9:
                a0 = math.atan2(start.y - center.y, start.x - center.x)
                a1 = math.atan2(end.y - center.y, end.x - center.x)
                self.canvas.add_geometry(Arc(center, radius, a0, a1))
            self.points = []
