"""Documento: contiene la topologia y el historial de undo/redo."""

from __future__ import annotations

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QUndoStack

from meshcad.core.topology.topology import Topology


class Document(QObject):
    """Estado del proyecto: topologia y pila de undo/redo."""

    topology_changed = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.topology = Topology()
        self.undo_stack = QUndoStack()

    def notify_change(self) -> None:
        self.topology_changed.emit()
