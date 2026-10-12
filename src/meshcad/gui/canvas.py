"""Lienzo de dibujo CAD (placeholder para la Fase 3)."""

from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView


class CadCanvas(QGraphicsView):
    """Vista grafica donde se dibujaran las entidades CAD."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
