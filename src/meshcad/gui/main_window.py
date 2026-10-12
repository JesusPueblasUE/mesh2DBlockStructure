"""Ventana principal de MeshCAD."""

import sys

from PyQt5.QtWidgets import QAction, QApplication, QMainWindow, QToolBar

from meshcad.gui.canvas import CadCanvas
from meshcad.gui.document import Document
from meshcad.gui.tools.line_tool import LineTool


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MeshCAD")
        self.resize(1024, 768)

        self.document = Document()
        self.canvas = CadCanvas(self.document)
        self.setCentralWidget(self.canvas)

        self._create_toolbar()

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("Herramientas", self)
        self.addToolBar(toolbar)

        self.action_select = QAction("Seleccionar", self)
        self.action_select.triggered.connect(lambda: self.canvas.set_tool(None))
        toolbar.addAction(self.action_select)

        self.action_line = QAction("Linea", self)
        self.action_line.triggered.connect(
            lambda: self.canvas.set_tool(LineTool(self.canvas))
        )
        toolbar.addAction(self.action_line)


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
