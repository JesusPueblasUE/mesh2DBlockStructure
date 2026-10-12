"""Bloque estructurado de 4 lados."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from meshcad.core.topology.block_side import BlockSide


@dataclass
class Block:
    """Bloque estructurado de 4 lados.

    Convenio de numeracion:
        lado 0 <-> lado 2 son opuestos
        lado 1 <-> lado 3 son opuestos

    La validacion de lados opuestos exige que tengan el mismo numero
    de nodos. Hasta que existan distribuciones, node_count es 0 en
    todos los lados y la validacion pasa trivialmente.
    """

    id: int
    sides: Tuple[BlockSide, BlockSide, BlockSide, BlockSide]

    def validate_opposite_sides(self) -> None:
        s0, s1, s2, s3 = self.sides
        if s0.node_count != s2.node_count:
            raise ValueError(
                "Los lados opuestos 0 y 2 deben tener el mismo numero "
                "de nodos: {} vs {}".format(s0.node_count, s2.node_count)
            )
        if s1.node_count != s3.node_count:
            raise ValueError(
                "Los lados opuestos 1 y 3 deben tener el mismo numero "
                "de nodos: {} vs {}".format(s1.node_count, s3.node_count)
            )

    def __repr__(self) -> str:
        return "Block(id={}, sides=[{}])".format(
            self.id, ", ".join(repr(s) for s in self.sides)
        )
