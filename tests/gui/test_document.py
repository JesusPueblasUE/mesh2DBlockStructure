from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.gui.document import Document


def test_document_starts_empty():
    doc = Document()
    assert len(doc.topology.vertices()) == 0
    assert len(doc.topology.edges()) == 0


def test_document_topology_changed_signal(qtbot):
    doc = Document()
    with qtbot.waitSignal(doc.topology_changed, timeout=1000):
        doc.notify_change()
