from meshcad.core.mesh.smoothing import SmoothingOptions
from meshcad.gui.main_window import MainWindow


def test_toolbar_controls_exist(qtbot):
    w = MainWindow(); qtbot.addWidget(w)
    assert w.orthogonal_layers_spin.value() == 2
    assert w.smoothing_iterations_spin.value() == 0


def test_options_update_without_apply(qtbot):
    w = MainWindow(); qtbot.addWidget(w)
    w.orthogonal_check.setChecked(True)
    w.orthogonal_layers_spin.setValue(4)
    w.smoothing_iterations_spin.setValue(35)
    w.smoothing_relaxation_spin.setValue(0.30)
    w.orthogonal_strength_spin.setValue(0.75)
    w._mesh_update_timer.stop()
    w._apply_live_mesh_options()
    assert w.document.mesh_improvement == SmoothingOptions(True, 4, 35, 0.30, 0.75)
