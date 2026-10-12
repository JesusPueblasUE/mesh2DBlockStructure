"""Loop cerrado: secuencia de aristas orientadas que forman un contorno."""

from __future__ import annotations

from typing import Iterator, List, Optional, Tuple

from meshcad.core.topology.edge import OrientedEdge
from meshcad.core.topology.topology import Topology


class Loop:
    """Contorno cerrado formado por aristas orientadas.

    Las aristas se referencian por id (no se copian), de modo que varios
    loops pueden compartir exactamente la misma arista.
    """

    def __init__(self, oriented_edges: Optional[List[OrientedEdge]] = None) -> None:
        self._edges: List[OrientedEdge] = list(oriented_edges or [])

    # ----------------------------- building ----------------------------- #

    def add_edge(self, edge_id: int, reversed: bool = False) -> None:
        self._edges.append(OrientedEdge(edge_id, reversed))

    @property
    def oriented_edges(self) -> List[OrientedEdge]:
        return list(self._edges)

    def __len__(self) -> int:
        return len(self._edges)

    def __iter__(self) -> Iterator[OrientedEdge]:
        return iter(self._edges)

    def __getitem__(self, index: int) -> OrientedEdge:
        return self._edges[index]

    # --------------------------- orientation ---------------------------- #

    def _endpoints(
        self, topology: Topology, oriented: OrientedEdge
    ) -> Tuple[int, int]:
        edge = topology.get_edge(oriented.edge_id)
        if oriented.reversed:
            return edge.end_vertex_id, edge.start_vertex_id
        return edge.start_vertex_id, edge.end_vertex_id

    def ordered_vertex_ids(self, topology: Topology) -> List[int]:
        """Ids de vertices en orden de recorrido, empezando por el primero."""
        if not self._edges:
            return []
        first_start, _ = self._endpoints(topology, self._edges[0])
        result = [first_start]
        for oe in self._edges:
            _, end = self._endpoints(topology, oe)
            result.append(end)
        return result

    # ----------------------------- validity ----------------------------- #

    def is_closed(self, topology: Topology) -> bool:
        if not self._edges:
            return False
        for oe in self._edges:
            if not topology.has_edge(oe.edge_id):
                return False
        first_start = None
        prev_end = None
        for i, oe in enumerate(self._edges):
            start, end = self._endpoints(topology, oe)
            if i == 0:
                first_start = start
            elif start != prev_end:
                return False
            prev_end = end
        return prev_end == first_start

    def validate(self, topology: Topology) -> None:
        if not self._edges:
            raise ValueError("El loop no tiene aristas")
        for oe in self._edges:
            if not topology.has_edge(oe.edge_id):
                raise ValueError(
                    "Arista {} no existe en la topologia".format(oe.edge_id)
                )
        if not self.is_closed(topology):
            raise ValueError("El loop no esta cerrado")

    # ------------------------------ metrics ----------------------------- #

    def length(self, topology: Topology) -> float:
        total = 0.0
        for oe in self._edges:
            total += topology.get_edge(oe.edge_id).geometry.length()
        return total

    def __repr__(self) -> str:
        return "Loop(edges={})".format(len(self._edges))
