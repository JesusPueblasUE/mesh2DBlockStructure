"""Lado de un bloque estructurado: secuencia de aristas orientadas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from meshcad.core.topology.edge import OrientedEdge


@dataclass
class BlockSide:
    """Un lado de un bloque estructurado.

    El lado es una secuencia de OrientedEdge que se recorre de principio
    a fin. Varias aristas pueden componer un mismo lado.

    node_count es el numero de nodos que tendra la malla a lo largo de
    este lado. De momento vale 0 (sin asignar) hasta la fase de
    distribuciones.
    """

    oriented_edges: Tuple[OrientedEdge, ...]
    node_count: int = 0

    def __len__(self) -> int:
        return len(self.oriented_edges)

    def edge_ids(self) -> List[int]:
        return [oe.edge_id for oe in self.oriented_edges]

    def __repr__(self) -> str:
        return "BlockSide(edges={}, node_count={})".format(
            self.edge_ids(), self.node_count
        )
