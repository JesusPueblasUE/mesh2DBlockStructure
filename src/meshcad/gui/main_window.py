import sys

from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow


class MainWindow(QMainWindow):
    """Ventana principal de MeshCAD."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MeshCAD")
        self.resize(1024, 768)

        placeholder = QLabel("MeshCAD - Fase 0: estructura inicial")
        placeholder.setStyleSheet("padding: 20px; font-size: 14px;")
        self.setCentralWidget(placeholder)


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
