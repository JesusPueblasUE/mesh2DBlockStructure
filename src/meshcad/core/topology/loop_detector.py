"""Deteccion automatica de loops simples en la topologia."""

from __future__ import annotations

from collections import defaultdict
from typing import List, Set, Tuple

from meshcad.core.topology.edge import OrientedEdge
from meshcad.core.topology.loop import Loop
from meshcad.core.topology.topology import Topology


def _canonical(edge_ids: Tuple[int, ...]) -> Tuple[int, ...]:
    """Clave canonica de un ciclo: minima entre todas las rotaciones y su inversa."""
    n = len(edge_ids)
    forms = []
    for i in range(n):
        forms.append(tuple(edge_ids[i:] + edge_ids[:i]))
    rev = tuple(reversed(edge_ids))
    for i in range(n):
        forms.append(tuple(rev[i:] + rev[:i]))
    return min(forms)


def find_loops(topology: Topology, max_loops: int = 50) -> List[Loop]:
    """Encuentra loops simples (ciclos sin vertices repetidos salvo el inicio).

    Devuelve una lista de Loop con los OrientedEdge ya orientados segun
    el recorrido encontrado.
    """
    adj = defaultdict(list)
    for e in topology.edges():
        adj[e.start_vertex_id].append((e.id, e.end_vertex_id, False))
        adj[e.end_vertex_id].append((e.id, e.start_vertex_id, True))

    loops_data: List[List[Tuple[int, bool]]] = []
    seen: Set[Tuple[int, ...]] = set()

    def dfs(start, current, path_oriented, path_vertices):
        if len(loops_data) >= max_loops:
            return
        for edge_id, neighbor, reversed_ in adj[current]:
            if any(oe[0] == edge_id for oe in path_oriented):
                continue
            if neighbor == start and len(path_oriented) >= 2:
                candidate = path_oriented + [(edge_id, reversed_)]
                key = _canonical(tuple(oe[0] for oe in candidate))
                if key not in seen:
                    seen.add(key)
                    loops_data.append(candidate)
                continue
            if neighbor in path_vertices:
                continue
            path_oriented.append((edge_id, reversed_))
            path_vertices.add(neighbor)
            dfs(start, neighbor, path_oriented, path_vertices)
            path_oriented.pop()
            path_vertices.remove(neighbor)

    for v in topology.vertices():
        dfs(v.id, v.id, [], {v.id})

    loops: List[Loop] = []
    for data in loops_data:
        loop = Loop()
        for edge_id, rev in data:
            loop.add_edge(edge_id, reversed=rev)
        loops.append(loop)
    return loops
