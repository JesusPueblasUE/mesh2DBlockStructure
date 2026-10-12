#!/usr/bin/env python3
"""
Fase 2 del proyecto MeshCAD: topologia CAD.

Crea los commits atomicos de la fase 2:
Vertex, Edge, OrientedEdge, Topology y Loop.

Uso:
    cd meshcad
    python phase2.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()


def check():
    if not (ROOT / "pyproject.toml").exists():
        print("ERROR: ejecuta este script desde la raiz del proyecto meshcad.")
        sys.exit(1)
    if not (ROOT / ".git").exists():
        print("ERROR: este directorio no es un repositorio git.")
        sys.exit(1)


def run(cmd):
    print("  $ " + " ".join(cmd))
    r = subprocess.run(cmd, cwd=str(ROOT))
    if r.returncode != 0:
        raise RuntimeError("Fallo: " + " ".join(cmd))


def write(rel, content):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print("  + " + rel)


def commit(stage, files, msg):
    print()
    print("== " + stage + " ==")
    for rel, content in files.items():
        write(rel, content)
    run(["git", "add", "."])
    run(["git", "commit", "-m", msg])


# =========================================================================== #
# COMMIT 6 - Vertex
# =========================================================================== #

VERTEX_PY = '''"""Vertice topologico: punto con identificador estable."""

from __future__ import annotations

from dataclasses import dataclass

from meshcad.core.geometry.point import Point2D


@dataclass(frozen=True)
class Vertex:
    """Vertice topologico.

    El id es asignado por el contenedor Topology. El punto es la
    representacion geometrica del vertice.
    """

    id: int
    point: Point2D

    def __repr__(self) -> str:
        return "Vertex(id={}, point={!r})".format(self.id, self.point)
'''

TOPOLOGY_INIT_STEP1 = '''"""Topologia CAD: Vertex, Edge, Loop, BlockSide, Block."""

from meshcad.core.topology.vertex import Vertex

__all__ = ["Vertex"]
'''

TEST_VERTEX = '''import pytest

from meshcad.core.geometry.point import Point2D
from meshcad.core.topology.vertex import Vertex


def test_create():
    v = Vertex(0, Point2D(1.0, 2.0))
    assert v.id == 0
    assert v.point == Point2D(1.0, 2.0)


def test_equality_by_value():
    a = Vertex(0, Point2D(1.0, 2.0))
    b = Vertex(0, Point2D(1.0, 2.0))
    c = Vertex(1, Point2D(1.0, 2.0))
    assert a == b
    assert a != c


def test_immutable():
    v = Vertex(0, Point2D(0.0, 0.0))
    with pytest.raises(Exception):
        v.id = 99
'''


# =========================================================================== #
# COMMIT 7 - Edge + OrientedEdge
# =========================================================================== #

EDGE_PY = '''"""Arista topologica y su uso orientado dentro de un loop."""

from __future__ import annotations

from dataclasses import dataclass

from meshcad.core.geometry.entity import GeometryEntity


@dataclass(frozen=True)
class Edge:
    """Arista topologica entre dos vertices.

    La geometria subyacente (Line, Arc, Spline) define la forma de la
    arista y va siempre en el sentido start_vertex -> end_vertex.
    Si un loop la recorre en sentido contrario, no se duplica la arista:
    se usa OrientedEdge con reversed=True.
    """

    id: int
    start_vertex_id: int
    end_vertex_id: int
    geometry: GeometryEntity

    def __repr__(self) -> str:
        return "Edge(id={}, v{} -> v{})".format(
            self.id, self.start_vertex_id, self.end_vertex_id
        )


@dataclass(frozen=True)
class OrientedEdge:
    """Uso concreto de una arista dentro de un loop.

    reversed=False: el loop recorre la arista en su sentido natural
                    (start_vertex -> end_vertex).
    reversed=True:  el loop la recorre al reves.
    """

    edge_id: int
    reversed: bool = False
'''

TOPOLOGY_INIT_STEP2 = '''"""Topologia CAD: Vertex, Edge, Loop, BlockSide, Block."""

from meshcad.core.topology.vertex import Vertex
from meshcad.core.topology.edge import Edge, OrientedEdge

__all__ = ["Vertex", "Edge", "OrientedEdge"]
'''

TEST_EDGE = '''import pytest

from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.topology.edge import Edge, OrientedEdge


def make_edge():
    return Edge(
        id=0,
        start_vertex_id=0,
        end_vertex_id=1,
        geometry=Line(Point2D(0, 0), Point2D(1, 0)),
    )


def test_create():
    e = make_edge()
    assert e.id == 0
    assert e.start_vertex_id == 0
    assert e.end_vertex_id == 1
    assert isinstance(e.geometry, Line)


def test_frozen():
    e = make_edge()
    with pytest.raises(Exception):
        e.id = 99


def test_oriented_default_forward():
    oe = OrientedEdge(edge_id=5)
    assert oe.edge_id == 5
    assert oe.reversed is False


def test_oriented_reversed():
    oe = OrientedEdge(edge_id=5, reversed=True)
    assert oe.edge_id == 5
    assert oe.reversed is True


def test_oriented_equality():
    assert OrientedEdge(3) == OrientedEdge(3)
    assert OrientedEdge(3) != OrientedEdge(3, reversed=True)
'''


# =========================================================================== #
# COMMIT 8 - Topology
# =========================================================================== #

TOPOLOGY_PY = '''"""Contenedor de vertices y aristas con identificadores unicos."""

from __future__ import annotations

from itertools import count
from typing import Dict, List, Optional

from meshcad.core.geometry.entity import GeometryEntity
from meshcad.core.geometry.point import Point2D
from meshcad.core.topology.edge import Edge
from meshcad.core.topology.vertex import Vertex

TOL = 1e-7


class Topology:
    """Almacen de vertices y aristas.

    Los loops no se guardan aqui: solo referencian aristas por id. Asi
    varios loops pueden compartir exactamente la misma arista sin duplicar
    geometria ni distribuciones de nodos.
    """

    def __init__(self) -> None:
        self._vertices: Dict[int, Vertex] = {}
        self._edges: Dict[int, Edge] = {}
        self._vertex_ids = count(0)
        self._edge_ids = count(0)

    # ----------------------------- vertices ----------------------------- #

    def add_vertex(self, point: Point2D) -> Vertex:
        v = Vertex(next(self._vertex_ids), point)
        self._vertices[v.id] = v
        return v

    def get_vertex(self, vertex_id: int) -> Vertex:
        try:
            return self._vertices[vertex_id]
        except KeyError:
            raise KeyError("Vertice {} no existe".format(vertex_id))

    def has_vertex(self, vertex_id: int) -> bool:
        return vertex_id in self._vertices

    def vertices(self) -> List[Vertex]:
        return list(self._vertices.values())

    def find_vertex_at(self, point: Point2D, tol: float = TOL) -> Optional[Vertex]:
        for v in self._vertices.values():
            if v.point.distance_to(point) <= tol:
                return v
        return None

    # ------------------------------ edges ------------------------------- #

    def add_edge(
        self,
        start_vertex: Vertex,
        end_vertex: Vertex,
        geometry: GeometryEntity,
    ) -> Edge:
        if not self.has_vertex(start_vertex.id):
            raise ValueError("start_vertex no pertenece a esta topologia")
        if not self.has_vertex(end_vertex.id):
            raise ValueError("end_vertex no pertenece a esta topologia")
        if geometry.start_point().distance_to(start_vertex.point) > TOL:
            raise ValueError(
                "El punto inicial de la geometria no coincide con start_vertex"
            )
        if geometry.end_point().distance_to(end_vertex.point) > TOL:
            raise ValueError(
                "El punto final de la geometria no coincide con end_vertex"
            )
        e = Edge(next(self._edge_ids), start_vertex.id, end_vertex.id, geometry)
        self._edges[e.id] = e
        return e

    def get_edge(self, edge_id: int) -> Edge:
        try:
            return self._edges[edge_id]
        except KeyError:
            raise KeyError("Arista {} no existe".format(edge_id))

    def has_edge(self, edge_id: int) -> bool:
        return edge_id in self._edges

    def edges(self) -> List[Edge]:
        return list(self._edges.values())

    # ------------------------------- misc ------------------------------- #

    def __len__(self) -> int:
        return len(self._vertices) + len(self._edges)

    def __repr__(self) -> str:
        return "Topology(vertices={}, edges={})".format(
            len(self._vertices), len(self._edges)
        )
'''

TOPOLOGY_INIT_STEP3 = '''"""Topologia CAD: Vertex, Edge, Loop, BlockSide, Block."""

from meshcad.core.topology.vertex import Vertex
from meshcad.core.topology.edge import Edge, OrientedEdge
from meshcad.core.topology.topology import Topology

__all__ = ["Vertex", "Edge", "OrientedEdge", "Topology"]
'''

TEST_TOPOLOGY = '''import pytest

from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.topology.topology import Topology


def test_add_vertex_unique_ids():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    assert v0.id == 0
    assert v1.id == 1
    assert v0.id != v1.id


def test_get_vertex():
    t = Topology()
    v = t.add_vertex(Point2D(2, 3))
    assert t.get_vertex(v.id) is v
    assert t.has_vertex(v.id)
    assert not t.has_vertex(999)


def test_get_vertex_missing_raises():
    t = Topology()
    with pytest.raises(KeyError):
        t.get_vertex(42)


def test_find_vertex_at():
    t = Topology()
    v = t.add_vertex(Point2D(1.0, 1.0))
    assert t.find_vertex_at(Point2D(1.0, 1.0)) is v
    assert t.find_vertex_at(Point2D(1.0 + 1e-10, 1.0)) is v
    assert t.find_vertex_at(Point2D(1.5, 1.5)) is None


def test_add_edge_valid():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    e = t.add_edge(v0, v1, Line(v0.point, v1.point))
    assert e.id == 0
    assert e.start_vertex_id == v0.id
    assert e.end_vertex_id == v1.id


def test_add_edge_geometry_must_match_start():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    with pytest.raises(ValueError):
        t.add_edge(v0, v1, Line(Point2D(5, 5), v1.point))


def test_add_edge_geometry_must_match_end():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    with pytest.raises(ValueError):
        t.add_edge(v0, v1, Line(v0.point, Point2D(9, 9)))


def test_add_edge_foreign_vertex_rejected():
    t1 = Topology()
    t2 = Topology()
    v0 = t2.add_vertex(Point2D(0, 0))
    v1 = t2.add_vertex(Point2D(1, 0))
    with pytest.raises(ValueError):
        t1.add_edge(v0, v1, Line(v0.point, v1.point))


def test_edges_unique_ids():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    e0 = t.add_edge(v0, v1, Line(v0.point, v1.point))
    e1 = t.add_edge(v1, v0, Line(v1.point, v0.point))
    assert e0.id != e1.id


def test_len_and_listing():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    t.add_edge(v0, v1, Line(v0.point, v1.point))
    assert len(t) == 3
    assert len(t.vertices()) == 2
    assert len(t.edges()) == 1
'''


# =========================================================================== #
# COMMIT 9 - Loop
# =========================================================================== #

LOOP_PY = '''"""Loop cerrado: secuencia de aristas orientadas que forman un contorno."""

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
'''

TOPOLOGY_INIT_STEP4 = '''"""Topologia CAD: Vertex, Edge, Loop, BlockSide, Block."""

from meshcad.core.topology.vertex import Vertex
from meshcad.core.topology.edge import Edge, OrientedEdge
from meshcad.core.topology.topology import Topology
from meshcad.core.topology.loop import Loop

__all__ = ["Vertex", "Edge", "OrientedEdge", "Topology", "Loop"]
'''

TEST_LOOP = '''import math

import pytest

from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.topology.loop import Loop
from meshcad.core.topology.topology import Topology


def make_triangle():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    v2 = t.add_vertex(Point2D(0, 1))
    e0 = t.add_edge(v0, v1, Line(v0.point, v1.point))
    e1 = t.add_edge(v1, v2, Line(v1.point, v2.point))
    e2 = t.add_edge(v2, v0, Line(v2.point, v0.point))
    return t, (v0, v1, v2), (e0, e1, e2)


def test_empty_loop():
    loop = Loop()
    assert len(loop) == 0
    t = Topology()
    assert not loop.is_closed(t)


def test_triangle_closed():
    t, (v0, v1, v2), (e0, e1, e2) = make_triangle()
    loop = Loop()
    loop.add_edge(e0.id)
    loop.add_edge(e1.id)
    loop.add_edge(e2.id)
    assert loop.is_closed(t)
    loop.validate(t)


def test_triangle_ordered_vertices():
    t, (v0, v1, v2), (e0, e1, e2) = make_triangle()
    loop = Loop()
    loop.add_edge(e0.id)
    loop.add_edge(e1.id)
    loop.add_edge(e2.id)
    assert loop.ordered_vertex_ids(t) == [v0.id, v1.id, v2.id, v0.id]


def test_open_chain_not_closed():
    t, (v0, v1, v2), (e0, e1, e2) = make_triangle()
    loop = Loop()
    loop.add_edge(e0.id)
    loop.add_edge(e1.id)
    assert not loop.is_closed(t)


def test_missing_edge_not_closed():
    t, _, (e0, _, _) = make_triangle()
    loop = Loop()
    loop.add_edge(e0.id)
    loop.add_edge(999)
    assert not loop.is_closed(t)


def test_validate_raises_for_open():
    t, _, (e0, e1, _) = make_triangle()
    loop = Loop()
    loop.add_edge(e0.id)
    loop.add_edge(e1.id)
    with pytest.raises(ValueError):
        loop.validate(t)


def test_triangle_all_reversed_is_closed():
    t, (v0, v1, v2), (e0, e1, e2) = make_triangle()
    loop = Loop()
    loop.add_edge(e2.id, reversed=True)
    loop.add_edge(e1.id, reversed=True)
    loop.add_edge(e0.id, reversed=True)
    assert loop.is_closed(t)
    # traversal: v0 -> v2 -> v1 -> v0
    assert loop.ordered_vertex_ids(t) == [v0.id, v2.id, v1.id, v0.id]


def test_mixed_orientation_closed():
    # Construimos un triangulo con e1 definido en sentido contrario
    # (v2 -> v1) para probar que reversed=True arregla la orientacion.
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    v2 = t.add_vertex(Point2D(0, 1))
    e0 = t.add_edge(v0, v1, Line(v0.point, v1.point))
    e1 = t.add_edge(v2, v1, Line(v2.point, v1.point))  # ojo, al reves
    e2 = t.add_edge(v2, v0, Line(v2.point, v0.point))

    loop = Loop()
    loop.add_edge(e0.id)
    loop.add_edge(e1.id, reversed=True)
    loop.add_edge(e2.id)
    assert loop.is_closed(t)
    assert loop.ordered_vertex_ids(t) == [v0.id, v1.id, v2.id, v0.id]


def test_length_triangle():
    t, _, (e0, e1, e2) = make_triangle()
    loop = Loop()
    loop.add_edge(e0.id)
    loop.add_edge(e1.id)
    loop.add_edge(e2.id)
    expected = 1.0 + math.sqrt(2.0) + 1.0
    assert math.isclose(loop.length(t), expected)
'''


# =========================================================================== #
# COMMIT 10 - Shared edges between loops
# =========================================================================== #

TEST_SHARED = '''"""Prueba que dos loops pueden compartir exactamente la misma arista.

Esta es la propiedad fundamental para el mallador: si dos bloques
comparten una arista, esa arista es un unico objeto Edge y por tanto
tendra una unica distribucion de nodos.
"""

from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.topology.loop import Loop
from meshcad.core.topology.topology import Topology


def build_two_squares():
    """Dos cuadrados que comparten la arista vertical central.

    Topologia (vertices):
        v2(0,1) --- v3(1,1) --- v4(2,1)
        |           |           |
        v0(0,0) --- v1(1,0) --- v5(2,0)

    Cuadrado izquierdo: v0 -> v1 -> v3 -> v2 -> v0
    Cuadrado derecho:   v1 -> v5 -> v4 -> v3 -> v1
    Arista compartida:  v1 -> v3
    """
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    v2 = t.add_vertex(Point2D(0, 1))
    v3 = t.add_vertex(Point2D(1, 1))
    v4 = t.add_vertex(Point2D(2, 1))
    v5 = t.add_vertex(Point2D(2, 0))

    e_bottom_left = t.add_edge(v0, v1, Line(v0.point, v1.point))
    e_left = t.add_edge(v0, v2, Line(v0.point, v2.point))
    e_top_left = t.add_edge(v2, v3, Line(v2.point, v3.point))
    e_shared = t.add_edge(v1, v3, Line(v1.point, v3.point))
    e_bottom_right = t.add_edge(v1, v5, Line(v1.point, v5.point))
    e_right = t.add_edge(v5, v4, Line(v5.point, v4.point))
    e_top_right = t.add_edge(v3, v4, Line(v3.point, v4.point))

    left = Loop()
    left.add_edge(e_bottom_left.id)
    left.add_edge(e_shared.id)
    left.add_edge(e_top_left.id, reversed=True)  # v3 -> v2
    left.add_edge(e_left.id, reversed=True)      # v2 -> v0

    right = Loop()
    right.add_edge(e_shared.id, reversed=True)   # v1 -> v3 invertida: v3 -> v1
    # En realidad queremos v1 -> v5 -> v4 -> v3 -> v1, veamos:
    # e_shared va de v1 a v3; la necesitamos en sentido v3 -> v1 -> reversed
    # Reconstruimos right desde v1:
    right = Loop()
    right.add_edge(e_bottom_right.id)            # v1 -> v5
    right.add_edge(e_right.id)                   # v5 -> v4
    right.add_edge(e_top_right.id, reversed=True)  # v4 -> v3
    right.add_edge(e_shared.id, reversed=True)   # v3 -> v1

    return t, left, right, e_shared


def test_left_square_is_closed():
    t, left, right, _ = build_two_squares()
    assert left.is_closed(t)
    left.validate(t)


def test_right_square_is_closed():
    t, left, right, _ = build_two_squares()
    assert right.is_closed(t)
    right.validate(t)


def test_shared_edge_is_the_same_object():
    t, left, right, e_shared = build_two_squares()
    # La arista compartida aparece en ambos loops con el mismo id.
    left_ids = [oe.edge_id for oe in left]
    right_ids = [oe.edge_id for oe in right]
    assert e_shared.id in left_ids
    assert e_shared.id in right_ids
    # Y es literalmente el mismo objeto en la topologia.
    assert t.get_edge(e_shared.id) is e_shared


def test_shared_edge_appears_once_in_topology():
    t, _, _, e_shared = build_two_squares()
    occurrences = sum(1 for e in t.edges() if e.id == e_shared.id)
    assert occurrences == 1
'''


# =========================================================================== #
# Ejecucion
# =========================================================================== #

def main():
    check()

    commit(
        "Commit 6/10: Vertex",
        {
            "src/meshcad/core/topology/vertex.py": VERTEX_PY,
            "src/meshcad/core/topology/__init__.py": TOPOLOGY_INIT_STEP1,
            "tests/core/topology/__init__.py": "",
            "tests/core/topology/test_vertex.py": TEST_VERTEX,
        },
        "feat(core): vertice topologico Vertex",
    )

    commit(
        "Commit 7/10: Edge + OrientedEdge",
        {
            "src/meshcad/core/topology/edge.py": EDGE_PY,
            "src/meshcad/core/topology/__init__.py": TOPOLOGY_INIT_STEP2,
            "tests/core/topology/test_edge.py": TEST_EDGE,
        },
        "feat(core): arista Edge y OrientedEdge",
    )

    commit(
        "Commit 8/10: Topology",
        {
            "src/meshcad/core/topology/topology.py": TOPOLOGY_PY,
            "src/meshcad/core/topology/__init__.py": TOPOLOGY_INIT_STEP3,
            "tests/core/topology/test_topology.py": TEST_TOPOLOGY,
        },
        "feat(core): contenedor Topology con IDs estables",
    )

    commit(
        "Commit 9/10: Loop",
        {
            "src/meshcad/core/topology/loop.py": LOOP_PY,
            "src/meshcad/core/topology/__init__.py": TOPOLOGY_INIT_STEP4,
            "tests/core/topology/test_loop.py": TEST_LOOP,
        },
        "feat(core): loop cerrado con validacion",
    )

    commit(
        "Commit 10/10: Shared edges",
        {
            "tests/core/topology/test_shared_edges.py": TEST_SHARED,
        },
        "test(core): aristas compartidas entre loops",
    )

    print()
    print("== Verificando todos los tests ==")
    run([sys.executable, "-m", "pytest", "-q"])

    print()
    print("== Historial ==")
    run(["git", "log", "--oneline", "--decorate"])

    print()
    print("Fase 2 completada.")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print()
        print("ERROR:", e)
        sys.exit(1)