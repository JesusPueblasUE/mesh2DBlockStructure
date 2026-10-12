"""Herramienta interactiva para dibujar segmentos de recta."""

from __future__ import annotations

from meshcad.core.geometry.line import Line
from meshcad.gui.tools.base import BaseTool


class LineTool(BaseTool):
    """Dos clics: inicio y fin."""

    def mouse_press(self, event) -> None:
        p = self._scene_point(event)
        self.points.append(p)

        if len(self.points) == 2:
            self.canvas.add_geometry(Line(self.points[0], self.points[1]))
            self.points = []
