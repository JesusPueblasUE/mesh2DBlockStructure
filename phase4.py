#!/usr/bin/env python3
"""
Fase 4 del proyecto MeshCAD: bloques estructurados de 4 lados.

Incluye tambien el cierre de la fase 3: deteccion de loops desde la GUI.

Uso:
    cd meshcad
    python phase4.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()


def check():
    if not (ROOT / "pyproject.toml").exists():
        print("ERROR: ejecuta este script desde la raiz del proyecto meshcad.")
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
# COMMIT 19 - BlockSide y Block
# =========================================================================== #

BLOCK_SIDE_PY = '''"""Lado de un bloque estructurado: secuencia de aristas orientadas."""

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
'''

BLOCK_PY = '''"""Bloque estructurado de 4 lados."""

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
'''

TOPOLOGY_INIT = '''"""Topologia CAD: Vertex, Edge, Loop, BlockSide, Block."""

from meshcad.core.topology.vertex import Vertex
from meshcad.core.topology.edge import Edge, OrientedEdge
from meshcad.core.topology.topology import Topology
from meshcad.core.topology.loop import Loop
from meshcad.core.topology.block_side import BlockSide
from meshcad.core.topology.block import Block

__all__ = [
    "Vertex",
    "Edge",
    "OrientedEdge",
    "Topology",
    "Loop",
    "BlockSide",
    "Block",
]
'''

TEST_BLOCK_SIDE = '''from meshcad.core.topology.block_side import BlockSide
from meshcad.core.topology.edge import OrientedEdge


def test_create_empty():
    side = BlockSide(oriented_edges=())
    assert len(side) == 0
    assert side.node_count == 0
    assert side.edge_ids() == []


def test_create_with_edges():
    side = BlockSide(
        oriented_edges=(OrientedEdge(0), OrientedEdge(1, reversed=True)),
        node_count=5,
    )
    assert len(side) == 2
    assert side.node_count == 5
    assert side.edge_ids() == [0, 1]


def test_node_count_default():
    side = BlockSide(oriented_edges=(OrientedEdge(0),))
    assert side.node_count == 0
'''

TEST_BLOCK = '''import pytest

from meshcad.core.topology.block import Block
from meshcad.core.topology.block_side import BlockSide
from meshcad.core.topology.edge import OrientedEdge


def make_sides(n0=0, n1=0, n2=0, n3=0):
    return (
        BlockSide((OrientedEdge(0),), node_count=n0),
        BlockSide((OrientedEdge(1),), node_count=n1),
        BlockSide((OrientedEdge(2),), node_count=n2),
        BlockSide((OrientedEdge(3),), node_count=n3),
    )


def test_create():
    b = Block(0, make_sides())
    assert b.id == 0
    assert len(b.sides) == 4


def test_validate_defaults_pass():
    b = Block(0, make_sides())
    b.validate_opposite_sides()


def test_validate_matching_counts_pass():
    b = Block(0, make_sides(5, 7, 5, 7))
    b.validate_opposite_sides()


def test_validate_mismatch_0_2_raises():
    b = Block(0, make_sides(5, 7, 6, 7))
    with pytest.raises(ValueError):
        b.validate_opposite_sides()


def test_validate_mismatch_1_3_raises():
    b = Block(0, make_sides(5, 7, 5, 8))
    with pytest.raises(ValueError):
        b.validate_opposite_sides()
'''


# =========================================================================== #
# COMMIT 20 - Loop.split_at_corners
# =========================================================================== #

LOOP_PY = '''"""Loop cerrado: secuencia de aristas orientadas que forman un contorno."""

from __future__ import annotations

from typing import Iterator, List, Optional, Sequence, Tuple

from meshcad.core.topology.block_side import BlockSide
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

    # ------------------------------ blocks ------------------------------ #

    def split_at_corners(
        self,
        topology: Topology,
        corner_vertex_ids: Sequence[int],
    ) -> Tuple[BlockSide, BlockSide, BlockSide, BlockSide]:
        """Divide el loop en 4 lados usando 4 vertices como esquinas.

        corner_vertex_ids puede venir en cualquier orden: se reordena
        segun su posicion a lo largo del loop.
        """
        if len(corner_vertex_ids) != 4:
            raise ValueError("Se necesitan exactamente 4 esquinas")
        if len(set(corner_vertex_ids)) != 4:
            raise ValueError("Las 4 esquinas deben ser distintas")

        n_edges = len(self._edges)
        if n_edges < 4:
            raise ValueError("Un loop con menos de 4 aristas no forma un bloque")

        vertex_path = self.ordered_vertex_ids(topology)

        positions = []
        for cid in corner_vertex_ids:
            idx = None
            for i in range(n_edges):
                if vertex_path[i] == cid:
                    idx = i
                    break
            if idx is None:
                raise ValueError(
                    "El vertice {} no pertenece al loop".format(cid)
                )
            positions.append((idx, cid))

        positions.sort()
        p0, p1, p2, p3 = [p for p, _ in positions]

        sides_edges = [
            self._edges[p0:p1],
            self._edges[p1:p2],
            self._edges[p2:p3],
            self._edges[p3:n_edges] + self._edges[0:p0],
        ]

        if any(len(s) == 0 for s in sides_edges):
            raise ValueError("Algun lado quedaria vacio: revisa las esquinas")

        return tuple(
            BlockSide(oriented_edges=tuple(s)) for s in sides_edges
        )

    def __repr__(self) -> str:
        return "Loop(edges={})".format(len(self._edges))
'''

TEST_SPLIT = '''import math

import pytest

from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.topology.loop import Loop
from meshcad.core.topology.topology import Topology


def make_square():
    """Cuadrado unitario con vertices v0..v3 y aristas e0..e3."""
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    v2 = t.add_vertex(Point2D(1, 1))
    v3 = t.add_vertex(Point2D(0, 1))
    e0 = t.add_edge(v0, v1, Line(v0.point, v1.point))
    e1 = t.add_edge(v1, v2, Line(v1.point, v2.point))
    e2 = t.add_edge(v2, v3, Line(v2.point, v3.point))
    e3 = t.add_edge(v3, v0, Line(v3.point, v0.point))
    loop = Loop()
    loop.add_edge(e0.id)
    loop.add_edge(e1.id)
    loop.add_edge(e2.id)
    loop.add_edge(e3.id)
    return t, (v0, v1, v2, v3), (e0, e1, e2, e3), loop


def test_split_square_into_four_sides():
    t, (v0, v1, v2, v3), (e0, e1, e2, e3), loop = make_square()
    sides = loop.split_at_corners(t, [v0.id, v1.id, v2.id, v3.id])
    assert len(sides) == 4
    assert sides[0].edge_ids() == [e0.id]
    assert sides[1].edge_ids() == [e1.id]
    assert sides[2].edge_ids() == [e2.id]
    assert sides[3].edge_ids() == [e3.id]


def test_split_accepts_any_order():
    t, (v0, v1, v2, v3), (e0, e1, e2, e3), loop = make_square()
    sides = loop.split_at_corners(t, [v2.id, v0.id, v3.id, v1.id])
    # Reordenado por posicion en el loop: v0, v1, v2, v3
    assert sides[0].edge_ids() == [e0.id]
    assert sides[1].edge_ids() == [e1.id]
    assert sides[2].edge_ids() == [e2.id]
    assert sides[3].edge_ids() == [e3.id]


def test_split_requires_four_corners():
    t, (v0, _, _, _), _, loop = make_square()
    with pytest.raises(ValueError):
        loop.split_at_corners(t, [v0.id])


def test_split_requires_distinct_corners():
    t, (v0, v1, _, _), _, loop = make_square()
    with pytest.raises(ValueError):
        loop.split_at_corners(t, [v0.id, v1.id, v1.id, v0.id])


def test_split_rejects_foreign_vertex():
    t, (_, _, _, _), _, loop = make_square()
    other = Topology()
    v_foreign = other.add_vertex(Point2D(99, 99))
    with pytest.raises(ValueError):
        loop.split_at_corners(t, [v_foreign.id, 1, 2, 3])


def test_split_with_multiple_edges_per_side():
    """Hexagono: v0..v5, se eligen esquinas cada 2 vertices."""
    t = Topology()
    coords = [
        (0.0, 0.0), (1.0, 0.0), (2.0, 0.5),
        (2.0, 1.5), (1.0, 2.0), (0.0, 1.5),
    ]
    verts = [t.add_vertex(Point2D(x, y)) for x, y in coords]
    edges = []
    for i in range(6):
        a = verts[i]
        b = verts[(i + 1) % 6]
        edges.append(t.add_edge(a, b, Line(a.point, b.point)))

    loop = Loop()
    for e in edges:
        loop.add_edge(e.id)

    # Esquinas: v0, v2, v3, v5
    sides = loop.split_at_corners(
        t, [verts[0].id, verts[2].id, verts[3].id, verts[5].id]
    )
    assert sides[0].edge_ids() == [edges[0].id, edges[1].id]
    assert sides[1].edge_ids() == [edges[2].id]
    assert sides[2].edge_ids() == [edges[3].id, edges[4].id]
    assert sides[3].edge_ids() == [edges[5].id]
'''


# =========================================================================== #
# COMMIT 21 - Loop detection
# =========================================================================== #

LOOP_DETECTOR_PY = '''"""Deteccion automatica de loops simples en la topologia."""

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
'''

TEST_DETECTOR = '''from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.topology.loop_detector import find_loops
from meshcad.core.topology.topology import Topology


def make_square():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    v2 = t.add_vertex(Point2D(1, 1))
    v3 = t.add_vertex(Point2D(0, 1))
    t.add_edge(v0, v1, Line(v0.point, v1.point))
    t.add_edge(v1, v2, Line(v1.point, v2.point))
    t.add_edge(v2, v3, Line(v2.point, v3.point))
    t.add_edge(v3, v0, Line(v3.point, v0.point))
    return t


def test_single_square():
    t = make_square()
    loops = find_loops(t)
    assert len(loops) == 1
    assert len(loops[0]) == 4
    assert loops[0].is_closed(t)


def test_open_chain_no_loops():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    v2 = t.add_vertex(Point2D(2, 0))
    t.add_edge(v0, v1, Line(v0.point, v1.point))
    t.add_edge(v1, v2, Line(v1.point, v2.point))
    assert find_loops(t) == []


def test_two_adjacent_squares_share_edge():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    v2 = t.add_vertex(Point2D(2, 0))
    v3 = t.add_vertex(Point2D(0, 1))
    v4 = t.add_vertex(Point2D(1, 1))
    v5 = t.add_vertex(Point2D(2, 1))
    t.add_edge(v0, v1, Line(v0.point, v1.point))
    t.add_edge(v1, v2, Line(v1.point, v2.point))
    t.add_edge(v2, v5, Line(v2.point, v5.point))
    t.add_edge(v5, v4, Line(v5.point, v4.point))
    t.add_edge(v4, v3, Line(v4.point, v3.point))
    t.add_edge(v3, v0, Line(v3.point, v0.point))
    t.add_edge(v1, v4, Line(v1.point, v4.point))  # arista compartida

    loops = find_loops(t)
    # Debe encontrar al menos los dos cuadrados y el rectangulo exterior.
    assert len(loops) >= 2
    for loop in loops:
        assert loop.is_closed(t)
'''


# =========================================================================== #
# COMMIT 22 - GUI: panel y herramienta de esquinas
# =========================================================================== #

DOCUMENT_PY = '''"""Documento: contiene la topologia, los bloques y el undo/redo."""

from __future__ import annotations

from typing import List

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QUndoStack

from meshcad.core.topology.block import Block
from meshcad.core.topology.topology import Topology


class Document(QObject):
    """Estado del proyecto."""

    topology_changed = pyqtSignal()
    blocks_changed = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.topology = Topology()
        self.blocks: List[Block] = []
        self._next_block_id = 0
        self.undo_stack = QUndoStack()

    def next_block_id(self) -> int:
        bid = self._next_block_id
        self._next_block_id += 1
        return bid

    def add_block(self, block: Block) -> None:
        self.blocks.append(block)
        self.blocks_changed.emit()

    def notify_change(self) -> None:
        self.topology_changed.emit()
'''

CORNER_PICKER_PY = '''"""Herramienta para elegir 4 esquinas de un loop."""

from __future__ import annotations

from typing import Callable, List

from meshcad.core.geometry.point import Point2D
from meshcad.gui.tools.base import BaseTool


class CornerPickerTool(BaseTool):
    """Pide al usuario 4 clics sobre vertices del loop activo.

    Al completar los 4, llama a on_complete(lista_ids_vertices).
    """

    def __init__(self, canvas, loop, on_complete: Callable[[List[int]], None]) -> None:
        super().__init__(canvas)
        self.loop = loop
        self.on_complete = on_complete
        self.corners: List[int] = []

    def mouse_press(self, event) -> None:
        pos = self.canvas.mapToScene(event.pos())
        p = Point2D(pos.x(), pos.y())
        vertex = self.canvas.snap_to_vertex(p)
        if vertex is None:
            return

        loop_vertex_ids = self.loop.ordered_vertex_ids(self.canvas.document.topology)
        if vertex.id not in loop_vertex_ids:
            return
        if vertex.id in self.corners:
            return

        self.corners.append(vertex.id)
        self.canvas.flash_vertex(vertex.id)

        if len(self.corners) == 4:
            self.on_complete(list(self.corners))
            self.cancel()

    def cancel(self) -> None:
        self.corners = []
        self.canvas.clear_preview()
'''

LOOPS_PANEL_PY = '''"""Panel lateral con la lista de loops detectados."""

from __future__ import annotations

from PyQt5.QtWidgets import (
    QDockWidget,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from meshcad.core.topology.block import Block
from meshcad.core.topology.loop_detector import find_loops
from meshcad.gui.document import Document
from meshcad.gui.tools.corner_picker import CornerPickerTool


class LoopsPanel(QDockWidget):
    """Dock con la lista de loops y el boton de crear bloque."""

    def __init__(self, document: Document, canvas, parent=None) -> None:
        super().__init__("Loops", parent)
        self.document = document
        self.canvas = canvas
        self.loops = []

        container = QWidget()
        layout = QVBoxLayout(container)

        self.find_button = QPushButton("Detectar loops")
        self.find_button.clicked.connect(self._on_find)
        layout.addWidget(self.find_button)

        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self._on_selection_changed)
        layout.addWidget(self.list_widget)

        self.create_button = QPushButton("Crear bloque del loop")
        self.create_button.clicked.connect(self._on_create_block)
        layout.addWidget(self.create_button)

        self.status = QLabel("Pulsa 'Detectar loops'.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.setWidget(container)

    # ------------------------------- slots ------------------------------- #

    def _on_find(self) -> None:
        self.loops = find_loops(self.document.topology)
        self.list_widget.clear()
        if not self.loops:
            self.status.setText("No se han detectado loops cerrados.")
            return
        for i, loop in enumerate(self.loops):
            item = QListWidgetItem("Loop {}: {} aristas".format(i, len(loop)))
            self.list_widget.addItem(item)
        self.status.setText(
            "Detectados {} loops. Selecciona uno y crea el bloque.".format(
                len(self.loops)
            )
        )

    def _on_selection_changed(self, row: int) -> None:
        if row < 0 or row >= len(self.loops):
            return
        self.canvas.highlight_loop(self.loops[row])

    def _on_create_block(self) -> None:
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self.loops):
            self.status.setText("Selecciona primero un loop.")
            return
        loop = self.loops[row]
        tool = CornerPickerTool(self.canvas, loop, self._on_corners_picked)
        self.canvas.set_tool(tool)
        self._active_loop = loop
        self.status.setText(
            "Haz clic en 4 vertices del loop (en cualquier orden)."
        )

    def _on_corners_picked(self, corner_ids) -> None:
        loop = self._active_loop
        try:
            sides = loop.split_at_corners(self.document.topology, corner_ids)
            block = Block(self.document.next_block_id(), sides)
            block.validate_opposite_sides()
        except ValueError as e:
            self.status.setText("Error: {}".format(e))
            return
        self.document.add_block(block)
        self.status.setText(
            "Bloque {} creado con lados [{}]".format(
                block.id, ", ".join(str(len(s)) for s in block.sides)
            )
        )
'''

CANVAS_PY = '''"""Lienzo CAD interactivo basado en QGraphicsView."""

from __future__ import annotations

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen
from PyQt5.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsScene,
    QGraphicsView,
)

from meshcad.core.geometry.point import Point2D
from meshcad.gui.document import Document
from meshcad.gui.items import GeometryItem

VERTEX_RADIUS = 4.0
SNAP_TOLERANCE = 8.0


class CadCanvas(QGraphicsView):
    def __init__(self, document: Document, parent=None) -> None:
        super().__init__(parent)
        self.document = document
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setMouseTracking(True)
        self.setBackgroundBrush(QBrush(QColor(250, 250, 252)))

        self.tool = None
        self._vertex_items = {}
        self._preview_item = None
        self._highlight_item = None

        self.document.topology_changed.connect(self._redraw_vertices)

    # ----------------------------- API publica --------------------------- #

    def set_tool(self, tool) -> None:
        if self.tool is not None:
            self.tool.cancel()
        self.tool = tool

    def add_geometry(self, geometry):
        topo = self.document.topology
        v_start = topo.find_vertex_at(geometry.start_point())
        if v_start is None:
            v_start = topo.add_vertex(geometry.start_point())
        v_end = topo.find_vertex_at(geometry.end_point())
        if v_end is None:
            v_end = topo.add_vertex(geometry.end_point())
        edge = topo.add_edge(v_start, v_end, geometry)
        item = GeometryItem(geometry)
        self.scene().addItem(item)
        self.document.notify_change()
        return edge

    def snap_to_vertex(self, scene_point: Point2D):
        topo = self.document.topology
        best = None
        best_dist = None
        for v in topo.vertices():
            d = v.point.distance_to(scene_point)
            if best_dist is None or d < best_dist:
                best = v
                best_dist = d
        if best is None:
            return None
        scale = self.transform().m11()
        if scale <= 0:
            return best
        tol_scene = SNAP_TOLERANCE / scale
        if best_dist is not None and best_dist <= tol_scene:
            return best
        return None

    # ----------------------------- preview ------------------------------- #

    def show_preview(self, geometry) -> None:
        self.clear_preview()
        if geometry is None:
            return
        item = GeometryItem(geometry, preview=True)
        self.scene().addItem(item)
        self._preview_item = item

    def clear_preview(self) -> None:
        if self._preview_item is not None:
            self.scene().removeItem(self._preview_item)
            self._preview_item = None

    # ---------------------------- highlight ------------------------------ #

    def highlight_loop(self, loop) -> None:
        from PyQt5.QtGui import QPainterPath

        self.clear_highlight()
        topo = self.document.topology
        path = QPainterPath()
        started = False
        for oe in loop:
            geom = topo.get_edge(oe.edge_id).geometry
            pts = geom.sample(30)
            if oe.reversed:
                pts = list(reversed(pts))
            for p in pts:
                if not started:
                    path.moveTo(p.x, p.y)
                    started = True
                else:
                    path.lineTo(p.x, p.y)

        from PyQt5.QtWidgets import QGraphicsPathItem

        item = QGraphicsPathItem(path)
        pen = QPen(QColor(60, 180, 60))
        pen.setWidthF(4.0)
        pen.setCosmetic(True)
        item.setPen(pen)
        item.setZValue(8.0)
        self.scene().addItem(item)
        self._highlight_item = item

    def clear_highlight(self) -> None:
        if self._highlight_item is not None:
            self.scene().removeItem(self._highlight_item)
            self._highlight_item = None

    def flash_vertex(self, vertex_id: int) -> None:
        item = self._vertex_items.get(vertex_id)
        if item is None:
            return
        original_brush = item.brush()
        item.setBrush(QBrush(QColor(60, 200, 60)))
        QTimer.singleShot(200, lambda: item.setBrush(original_brush))

    # ------------------------------- eventos ----------------------------- #

    def mousePressEvent(self, event) -> None:
        if self.tool is not None:
            self.tool.mouse_press(event)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self.tool is not None:
            self.tool.mouse_move(event)
        super().mouseMoveEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape and self.tool is not None:
            self.tool.cancel()
            self.tool = None
            event.accept()
            return
        super().keyPressEvent(event)

    # --------------------------- dibujo interno -------------------------- #

    def _redraw_vertices(self) -> None:
        for item in self._vertex_items.values():
            self.scene().removeItem(item)
        self._vertex_items.clear()

        pen = QPen(QColor(200, 40, 40))
        pen.setWidthF(1.0)
        brush = QBrush(QColor(255, 220, 220))
        for v in self.document.topology.vertices():
            item = QGraphicsEllipseItem(
                v.point.x - VERTEX_RADIUS,
                v.point.y - VERTEX_RADIUS,
                2 * VERTEX_RADIUS,
                2 * VERTEX_RADIUS,
            )
            item.setPen(pen)
            item.setBrush(brush)
            item.setZValue(10.0)
            self.scene().addItem(item)
            self._vertex_items[v.id] = item
'''

MAIN_WINDOW_PY = '''"""Ventana principal de MeshCAD."""

import sys

from PyQt5.QtWidgets import QAction, QApplication, QMainWindow, QToolBar

from meshcad.gui.canvas import CadCanvas
from meshcad.gui.document import Document
from meshcad.gui.loops_panel import LoopsPanel
from meshcad.gui.tools.arc_tool import ArcTool
from meshcad.gui.tools.line_tool import LineTool
from meshcad.gui.tools.spline_tool import SplineTool


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MeshCAD")
        self.resize(1280, 768)

        self.document = Document()
        self.canvas = CadCanvas(self.document)
        self.setCentralWidget(self.canvas)

        self.loops_panel = LoopsPanel(self.document, self.canvas, self)
        self.addDockWidget(1, self.loops_panel)

        self._create_toolbar()

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("Herramientas", self)
        self.addToolBar(toolbar)

        self.action_select = QAction("Seleccionar", self)
        self.action_select.triggered.connect(lambda: self.canvas.set_tool(None))
        toolbar.addAction(self.action_select)

        self.action_line = QAction("Linea", self)
        self.action_line.triggered.connect(
            lambda: self.canvas.set_tool(LineTool(self.canvas))
        )
        toolbar.addAction(self.action_line)

        self.action_arc = QAction("Arco", self)
        self.action_arc.triggered.connect(
            lambda: self.canvas.set_tool(ArcTool(self.canvas))
        )
        toolbar.addAction(self.action_arc)

        self.action_spline = QAction("Spline", self)
        self.action_spline.triggered.connect(
            lambda: self.canvas.set_tool(SplineTool(self.canvas))
        )
        toolbar.addAction(self.action_spline)


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
'''

TEST_DOCUMENT = '''from meshcad.core.topology.block import Block
from meshcad.core.topology.block_side import BlockSide
from meshcad.core.topology.edge import OrientedEdge
from meshcad.gui.document import Document


def test_document_starts_empty():
    doc = Document()
    assert len(doc.topology.vertices()) == 0
    assert len(doc.blocks) == 0


def test_next_block_id_is_monotonic():
    doc = Document()
    assert doc.next_block_id() == 0
    assert doc.next_block_id() == 1
    assert doc.next_block_id() == 2


def test_add_block_emits_signal(qtbot):
    doc = Document()
    sides = tuple(
        BlockSide((OrientedEdge(i),)) for i in range(4)
    )
    block = Block(0, sides)
    with qtbot.waitSignal(doc.blocks_changed, timeout=1000):
        doc.add_block(block)
    assert len(doc.blocks) == 1
'''


# =========================================================================== #
# Ejecucion
# =========================================================================== #

def main():
    check()

    commit(
        "Commit 19/23: BlockSide y Block",
        {
            "src/meshcad/core/topology/block_side.py": BLOCK_SIDE_PY,
            "src/meshcad/core/topology/block.py": BLOCK_PY,
            "src/meshcad/core/topology/__init__.py": TOPOLOGY_INIT,
            "tests/core/topology/test_block_side.py": TEST_BLOCK_SIDE,
            "tests/core/topology/test_block.py": TEST_BLOCK,
        },
        "feat(core): BlockSide y Block estructurado de 4 lados",
    )

    commit(
        "Commit 20/23: Loop.split_at_corners",
        {
            "src/meshcad/core/topology/loop.py": LOOP_PY,
            "tests/core/topology/test_split.py": TEST_SPLIT,
        },
        "feat(core): dividir Loop en 4 BlockSide por esquinas",
    )

    commit(
        "Commit 21/23: Deteccion de loops",
        {
            "src/meshcad/core/topology/loop_detector.py": LOOP_DETECTOR_PY,
            "tests/core/topology/test_loop_detector.py": TEST_DETECTOR,
        },
        "feat(core): deteccion automatica de loops cerrados",
    )

    commit(
        "Commit 22/23: Herramienta de esquinas",
        {
            "src/meshcad/gui/tools/corner_picker.py": CORNER_PICKER_PY,
        },
        "feat(gui): herramienta para elegir 4 esquinas de un loop",
    )

    commit(
        "Commit 23/23: Panel de loops y creacion de bloques",
        {
            "src/meshcad/gui/document.py": DOCUMENT_PY,
            "src/meshcad/gui/canvas.py": CANVAS_PY,
            "src/meshcad/gui/loops_panel.py": LOOPS_PANEL_PY,
            "src/meshcad/gui/main_window.py": MAIN_WINDOW_PY,
            "tests/gui/test_document.py": TEST_DOCUMENT,
        },
        "feat(gui): panel de loops y creacion de bloques desde la GUI",
    )

    print()
    print("== Verificando todos los tests ==")
    run([sys.executable, "-m", "pytest", "-q"])

    print()
    print("== Historial ==")
    run(["git", "log", "--oneline", "--decorate"])

    print()
    print("Fase 4 completada. Ejecuta 'python -m meshcad'.")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print()
        print("ERROR:", e)
        sys.exit(1)