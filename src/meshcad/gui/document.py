"""Documento: estado del proyecto (topologia, malla y bloques)."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QUndoStack

from meshcad.core.mesh.generator import BlockMesh, mesh_block
from meshcad.core.mesh.model import EdgeMeshSpec, MeshModel
from meshcad.core.topology.block import Block
from meshcad.core.topology.topology import Topology

FORMAT = "meshcad-project"
FORMAT_VERSION = 1


class Document(QObject):
    """Estado del proyecto."""

    topology_changed = pyqtSignal()
    mesh_changed = pyqtSignal()
    blocks_changed = pyqtSignal()
    mesh_generated = pyqtSignal()
    project_replaced = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.topology = Topology()
        self.mesh = MeshModel()
        self.blocks: List[Block] = []
        self.block_meshes: List[BlockMesh] = []
        self._next_block_id = 0
        self.undo_stack = QUndoStack()

    # ----------------------------- topology ----------------------------- #

    def notify_change(self) -> None:
        self.topology_changed.emit()
        self.recompute_blocks()

    # ------------------------------ blocks ------------------------------ #

    def next_block_id(self) -> int:
        bid = self._next_block_id
        self._next_block_id += 1
        return bid

    def add_block(self, block: Block) -> None:
        self.blocks.append(block)
        self.recompute_blocks()

    def recompute_blocks(self) -> None:
        for block in self.blocks:
            for side in block.sides:
                side.node_count = self.mesh.side_node_count(side)
        self.blocks_changed.emit()

    # ------------------------------- mesh ------------------------------- #

    def set_edge_spec(self, spec: EdgeMeshSpec) -> None:
        self.mesh.set_spec(spec)
        self.mesh_changed.emit()
        self.recompute_blocks()

    def generate_mesh(self) -> Tuple[List[BlockMesh], List[str]]:
        self.block_meshes = []
        errors: List[str] = []
        for block in self.blocks:
            try:
                bm = mesh_block(block, self.topology, self.mesh)
            except ValueError as e:
                errors.append("Bloque {}: {}".format(block.id, e))
                continue
            self.block_meshes.append(bm)
        self.mesh_generated.emit()
        return self.block_meshes, errors

    # ---------------------------- persistencia -------------------------- #

    def to_dict(self) -> Dict[str, Any]:
        from meshcad.io.json_io import (
            block_to_dict,
            edge_spec_to_dict,
            topology_to_dict,
        )

        return {
            "format": FORMAT,
            "version": FORMAT_VERSION,
            "topology": topology_to_dict(self.topology),
            "edge_specs": [
                edge_spec_to_dict(s) for s in self.mesh.edge_specs.values()
            ],
            "blocks": [block_to_dict(b) for b in self.blocks],
            "next_block_id": self._next_block_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        from meshcad.io.json_io import (
            block_from_dict,
            edge_spec_from_dict,
            topology_from_dict,
        )

        fmt = data.get("format")
        if fmt != FORMAT:
            raise ValueError(
                "Formato desconocido: {!r} (esperado {!r})".format(fmt, FORMAT)
            )

        doc = cls()
        doc.topology = topology_from_dict(data["topology"])
        for sd in data.get("edge_specs", []):
            doc.mesh.set_spec(edge_spec_from_dict(sd))
        doc.blocks = [block_from_dict(bd) for bd in data.get("blocks", [])]
        doc._next_block_id = int(
            data.get("next_block_id", len(doc.blocks))
        )
        doc.recompute_blocks()
        return doc

    def load_from(self, other: "Document") -> None:
        """Reemplaza el contenido manteniendo la identidad del Document.

        Necesario para que la GUI no tenga que reconectar todas las
        senales de canvas y paneles.
        """
        self.topology = other.topology
        self.mesh = other.mesh
        self.blocks = other.blocks
        self._next_block_id = other._next_block_id
        self.block_meshes = []
        self.topology_changed.emit()
        self.mesh_changed.emit()
        self.recompute_blocks()
        self.project_replaced.emit()
