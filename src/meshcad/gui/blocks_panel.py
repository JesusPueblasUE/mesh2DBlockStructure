"""Panel con la lista de bloques y el estado de sus lados opuestos."""

from __future__ import annotations
from PyQt5.QtWidgets import QDockWidget, QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget, QPushButton, QAbstractItemView
from meshcad.gui.document import Document


class BlocksPanel(QDockWidget):
    def __init__(self, document: Document, parent=None) -> None:
        super().__init__("Bloques", parent)
        self.document = document

        container = QWidget()
        layout = QVBoxLayout(container)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.list_widget)

        self.delete_button = QPushButton("Eliminar bloque seleccionado")
        self.delete_button.clicked.connect(self._on_delete)
        layout.addWidget(self.delete_button)

        self.status = QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.setWidget(container)

        self.document.blocks_changed.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        self.list_widget.clear()
        n_ok, n_bad = 0, 0
        for block in self.document.blocks:
            n0, n1, n2, n3 = [s.node_count for s in block.sides]
            ok_02 = (n0 == n2)
            ok_13 = (n1 == n3)
            if ok_02 and ok_13:
                tag = "OK"
                n_ok += 1
                detail = "(nodos {} x {})".format(n0, n1)
            else:
                tag = "DESAJUSTE"
                n_bad += 1
                msgs = []
                if not ok_02: msgs.append("lados 0/2: {} vs {}".format(n0, n2))
                if not ok_13: msgs.append("lados 1/3: {} vs {}".format(n1, n3))
                detail = "; ".join(msgs)

            item = QListWidgetItem("Bloque {}: {} {}".format(block.id, tag, detail))
            self.list_widget.addItem(item)

        if not self.document.blocks:
            self.status.setText("Sin bloques todavia.")
        else:
            self.status.setText("{} bloques: {} OK, {} con desajustes".format(len(self.document.blocks), n_ok, n_bad))

    def _on_delete(self) -> None:
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self.document.blocks):
            self.status.setText("Selecciona un bloque para borrar.")
            return
        block = self.document.blocks[row]
        self.document.remove_block(block.id)
        self.refresh()
