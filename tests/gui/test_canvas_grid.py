from meshcad.gui.canvas import CadCanvas
from meshcad.gui.document import Document


def test_toggle_grid(qtbot):
    doc = Document()
    canvas = CadCanvas(doc)
    qtbot.addWidget(canvas)
    assert canvas.show_grid is True
    canvas.show_grid = False
    assert canvas.show_grid is False
