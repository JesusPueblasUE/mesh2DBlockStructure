"""Clase base de las herramientas interactivas."""

from __future__ import annotations

from typing import List

from meshcad.core.geometry.point import Point2D


class BaseTool:
    """Interfaz comun a todas las herramientas interactivas.

    La herramienta recibe los eventos de raton del canvas. Acumula
    puntos hasta tener suficientes y luego llama a canvas.add_geometry.
    """

    def __init__(self, canvas) -> None:
        self.canvas = canvas
        self.points: List[Point2D] = []

    def mouse_press(self, event) -> None:  # pragma: no cover - abstracto
        raise NotImplementedError

    def mouse_move(self, event) -> None:
        return None

    def cancel(self) -> None:
        self.points = []

    def _scene_point(self, event) -> Point2D:
        pos = self.canvas.mapToScene(event.pos())
        p = Point2D(pos.x(), pos.y())
        snapped = self.canvas.snap_to_vertex(p)
        if snapped is not None:
            return snapped.point
        return p
