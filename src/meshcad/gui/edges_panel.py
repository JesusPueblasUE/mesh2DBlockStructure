"""Panel para editar la especificacion de malla de cada arista."""

from __future__ import annotations

from PyQt5.QtWidgets import (
    QComboBox,
    QDockWidget,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from meshcad.core.mesh.distribution import (
    BiasedDistribution,
    UniformDistribution,
)
from meshcad.core.mesh.model import EdgeMeshSpec
from meshcad.gui.document import Document


class EdgesPanel(QDockWidget):
    """Dock con la lista de aristas y sus propiedades de malla."""

    def __init__(self, document: Document, parent=None) -> None:
        super().__init__("Distribuciones", parent)
        self.document = document

        container = QWidget()
        layout = QVBoxLayout(container)

        self.refresh_button = QPushButton("Refrescar aristas")
        self.refresh_button.clicked.connect(self.refresh)
        layout.addWidget(self.refresh_button)

        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self._on_selection_changed)
        layout.addWidget(self.list_widget)

        form = QFormLayout()

        self.nodes_spin = QSpinBox()
        self.nodes_spin.setRange(2, 10000)
        self.nodes_spin.setValue(5)
        form.addRow("Nodos:", self.nodes_spin)

        self.dist_combo = QComboBox()
        self.dist_combo.addItems(["Uniforme", "Sesgada"])
        self.dist_combo.currentIndexChanged.connect(self._on_dist_changed)
        form.addRow("Distribucion:", self.dist_combo)

        self.bias_spin = QDoubleSpinBox()
        self.bias_spin.setRange(0.01, 100.0)
        self.bias_spin.setValue(2.0)
        self.bias_spin.setSingleStep(0.1)
        self.bias_spin.setEnabled(False)
        form.addRow("Bias:", self.bias_spin)

        layout.addLayout(form)

        self.apply_button = QPushButton("Aplicar")
        self.apply_button.clicked.connect(self._on_apply)
        layout.addWidget(self.apply_button)

        self.status = QLabel("Refresca para ver las aristas.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.setWidget(container)

    # ------------------------------ slots ------------------------------- #

    def refresh(self) -> None:
        self.list_widget.clear()
        for edge in self.document.topology.edges():
            spec = self.document.mesh.get_spec(edge.id)
            label = "Edge {}: v{}->v{}, {} nodos, {}".format(
                edge.id,
                edge.start_vertex_id,
                edge.end_vertex_id,
                spec.n_nodes,
                self._dist_name(spec.distribution),
            )
            self.list_widget.addItem(QListWidgetItem(label))
        if self.list_widget.count() == 0:
            self.status.setText("No hay aristas todavia.")
        else:
            self.status.setText(
                "{} aristas. Selecciona una y edita sus propiedades.".format(
                    self.list_widget.count()
                )
            )

    def _on_selection_changed(self, row: int) -> None:
        edges = self.document.topology.edges()
        if row < 0 or row >= len(edges):
            return
        spec = self.document.mesh.get_spec(edges[row].id)
        self.nodes_spin.setValue(spec.n_nodes)
        if isinstance(spec.distribution, BiasedDistribution):
            self.dist_combo.setCurrentText("Sesgada")
            self.bias_spin.setValue(spec.distribution.bias)
            self.bias_spin.setEnabled(True)
        else:
            self.dist_combo.setCurrentText("Uniforme")
            self.bias_spin.setEnabled(False)

    def _on_dist_changed(self, index: int) -> None:
        self.bias_spin.setEnabled(index == 1)

    def _on_apply(self) -> None:
        row = self.list_widget.currentRow()
        edges = self.document.topology.edges()
        if row < 0 or row >= len(edges):
            self.status.setText("Selecciona primero una arista.")
            return
        edge = edges[row]
        if self.dist_combo.currentText() == "Sesgada":
            dist = BiasedDistribution(bias=self.bias_spin.value())
        else:
            dist = UniformDistribution()
        spec = EdgeMeshSpec(edge.id, self.nodes_spin.value(), dist)
        self.document.set_edge_spec(spec)
        self.refresh()
        self.list_widget.setCurrentRow(row)
        self.status.setText("Arista {} actualizada.".format(edge.id))

    @staticmethod
    def _dist_name(dist):
        if isinstance(dist, BiasedDistribution):
            return "sesgada({:g})".format(dist.bias)
        return "uniforme"
