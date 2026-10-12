"""Documento: contiene la topologia, los bloques y el undo/redo."""

from __future__ import annotations

from typing import List

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QUndoStack

from meshcad.core.topology.block import Block
from meshcad.core.topology.topology import Topology


class Document(QObject):
    """Estado del proyecto."""

    topology_changed = pyqtSignal()
    blocks_changed = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.topology = Topology()
        self.blocks: List[Block] = []
        self._next_block_id = 0
        self.undo_stack = QUndoStack()

    def next_block_id(self) -> int:
        bid = self._next_block_id
        self._next_block_id += 1
        return bid

    def add_block(self, block: Block) -> None:
        self.blocks.append(block)
        self.blocks_changed.emit()

    def notify_change(self) -> None:
        self.topology_changed.emit()
