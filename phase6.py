#!/usr/bin/env python3
"""
Fase 6 del proyecto MeshCAD: generacion de malla estructurada.

Crea los commits atomicos de la fase 6:
TFI, BlockMesh, generador, integracion en Document y GUI.

Uso:
    cd meshcad
    python phase6.py
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
# COMMIT 30 - TFI
# =========================================================================== #

TFI_PY = '''"""Interpolacion transfinita (TFI) para un cuadrilatero."""

from __future__ import annotations

from typing import List, Sequence

from meshcad.core.geometry.point import Point2D


def tfi_grid(
    south: Sequence[Point2D],
    east: Sequence[Point2D],
    north: Sequence[Point2D],
    west: Sequence[Point2D],
) -> List[List[Point2D]]:
    """Genera una rejilla estructurada por interpolacion transfinita.

    Convenio de esquinas y sentidos (siempre segun el recorrido del loop):
        south: c0 -> c1 (N_u puntos). Es el lado 0 del bloque.
        east:  c1 -> c2 (N_v puntos). Es el lado 1 del bloque.
        north: c2 -> c3 (N_u puntos). Es el lado 2 del bloque.
        west:  c3 -> c0 (N_v puntos). Es el lado 3 del bloque.

    Devuelve grid[j][i] con j en [0, N_v), i en [0, N_u).
    grid[0][0] = c0, grid[0][N_u-1] = c1,
    grid[N_v-1][N_u-1] = c2, grid[N_v-1][0] = c3.
    """
    n_u = len(south)
    n_v = len(east)

    if len(north) != n_u:
        raise ValueError(
            "Los lados 0 y 2 deben tener el mismo numero de nodos: {} vs {}".format(
                n_u, len(north)
            )
        )
    if len(west) != n_v:
        raise ValueError(
            "Los lados 1 y 3 deben tener el mismo numero de nodos: {} vs {}".format(
                n_v, len(west)
            )
        )
    if n_u < 2 or n_v < 2:
        raise ValueError("Cada lado necesita al menos 2 nodos")

    # Esquinas
    c0 = south[0]
    c1 = south[-1]
    c2 = north[0]
    c3 = north[-1]

    # Reordenamos los lados 2 y 3 para que vayan en el sentido del grid:
    # north debe ir c3 -> c2 (o sea, recorrer el lado 2 al reves),
    # west debe ir c0 -> c3 (recorrer el lado 3 al reves).
    north_rev = list(reversed(north))
    west_rev = list(reversed(west))

    grid: List[List[Point2D]] = []
    for j in range(n_v):
        v = j / (n_v - 1)
        row: List[Point2D] = []
        for i in range(n_u):
            u = i / (n_u - 1)

            s = south[i]
            n = north_rev[i]  # norte en (u, 1)
            w = west_rev[j]   # oeste en (0, v)
            e = east[j]       # este en (1, v)

            # Correccion bilineal en las esquinas
            bx = (
                (1.0 - u) * (1.0 - v) * c0.x
                + u * (1.0 - v) * c1.x
                + u * v * c2.x
                + (1.0 - u) * v * c3.x
            )
            by = (
                (1.0 - u) * (1.0 - v) * c0.y
                + u * (1.0 - v) * c1.y
                + u * v * c2.y
                + (1.0 - u) * v * c3.y
            )

            x = (
                (1.0 - v) * s.x
                + v * n.x
                + (1.0 - u) * w.x
                + u * e.x
                - bx
            )
            y = (
                (1.0 - v) * s.y
                + v * n.y
                + (1.0 - u) * w.y
                + u * e.y
                - by
            )
            row.append(Point2D(x, y))
        grid.append(row)
    return grid
'''

TEST_TFI = '''import math

import pytest

from meshcad.core.geometry.point import Point2D
from meshcad.core.mesh.tfi import tfi_grid


def make_rect_sides(n_u=3, n_v=4):
    # Rectangulo [0, 1] x [0, 2]
    c0 = Point2D(0, 0)
    c1 = Point2D(1, 0)
    c2 = Point2D(1, 2)
    c3 = Point2D(0, 2)

    south = [Point2D(i / (n_u - 1), 0.0) for i in range(n_u)]
    east = [Point2D(1.0, 2.0 * j / (n_v - 1)) for j in range(n_v)]
    north = [Point2D(1.0 - i / (n_u - 1), 2.0) for i in range(n_u)]  # c2 -> c3
    west = [Point2D(0.0, 2.0 - 2.0 * j / (n_v - 1)) for j in range(n_v)]  # c3 -> c0
    return south, east, north, west


def test_grid_dimensions():
    s, e, n, w = make_rect_sides(3, 4)
    grid = tfi_grid(s, e, n, w)
    assert len(grid) == 4       # n_v rows
    assert len(grid[0]) == 3    # n_u columns


def test_grid_corners():
    s, e, n, w = make_rect_sides(3, 4)
    grid = tfi_grid(s, e, n, w)
    assert grid[0][0] == Point2D(0, 0)      # c0
    assert grid[0][-1] == Point2D(1, 0)     # c1
    assert grid[-1][-1] == Point2D(1, 2)    # c2
    assert grid[-1][0] == Point2D(0, 2)     # c3


def test_grid_boundaries_match_sides():
    s, e, n, w = make_rect_sides(5, 6)
    grid = tfi_grid(s, e, n, w)
    n_u = len(s)
    n_v = len(e)

    # Sur: fila 0 == south
    for i in range(n_u):
        assert math.isclose(grid[0][i].x, s[i].x)
        assert math.isclose(grid[0][i].y, s[i].y)

    # Este: columna n_u-1 == east
    for j in range(n_v):
        assert math.isclose(grid[j][n_u - 1].x, e[j].x)
        assert math.isclose(grid[j][n_u - 1].y, e[j].y)

    # Norte: fila n_v-1 == north reversed
    for i in range(n_u):
        assert math.isclose(grid[n_v - 1][i].x, n[n_u - 1 - i].x)
        assert math.isclose(grid[n_v - 1][i].y, n[n_u - 1 - i].y)

    # Oeste: columna 0 == west reversed
    for j in range(n_v):
        assert math.isclose(grid[j][0].x, w[n_v - 1 - j].x)
        assert math.isclose(grid[j][0].y, w[n_v - 1 - j].y)


def test_rectangle_interior_is_cartesian():
    # En un rectangulo con distribucion uniforme, la malla debe ser cartesiana.
    s, e, n, w = make_rect_sides(4, 5)
    grid = tfi_grid(s, e, n, w)
    for j in range(len(grid)):
        for i in range(len(grid[0])):
            expected_x = i / (len(grid[0]) - 1)
            expected_y = 2.0 * j / (len(grid) - 1)
            assert math.isclose(grid[j][i].x, expected_x)
            assert math.isclose(grid[j][i].y, expected_y)


def test_requires_matching_counts():
    s = [Point2D(0, 0), Point2D(1, 0), Point2D(2, 0)]
    e = [Point2D(2, 0), Point2D(2, 1)]
    n_wrong = [Point2D(2, 1), Point2D(0, 1)]  # solo 2 puntos en vez de 3
    w = [Point2D(0, 1), Point2D(0, 0)]
    with pytest.raises(ValueError):
        tfi_grid(s, e, n_wrong, w)


def test_requires_min_two_points():
    with pytest.raises(ValueError):
        tfi_grid([Point2D(0, 0)], [], [], [])
'''

MESH_INIT_STEP30 = '''"""Generacion de malla estructurada y distribuciones de nodos."""

from meshcad.core.mesh.distribution import (
    BiasedDistribution,
    NodeDistribution,
    UniformDistribution,
)
from meshcad.core.mesh.model import EdgeMeshSpec, MeshModel, DEFAULT_N_NODES
from meshcad.core.mesh.tfi import tfi_grid

__all__ = [
    "NodeDistribution",
    "UniformDistribution",
    "BiasedDistribution",
    "EdgeMeshSpec",
    "MeshModel",
    "DEFAULT_N_NODES",
    "tfi_grid",
]
'''


# =========================================================================== #
# COMMIT 31 - BlockMesh y mesh_block
# =========================================================================== #

GENERATOR_PY = '''"""Generacion de mallas estructuradas por bloque."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from meshcad.core.geometry.point import Point2D
from meshcad.core.mesh.model import MeshModel
from meshcad.core.mesh.tfi import tfi_grid
from meshcad.core.topology.block import Block
from meshcad.core.topology.topology import Topology


@dataclass
class BlockMesh:
    """Malla estructurada de un bloque.

    grid[j][i] con j en [0, n_v) e i en [0, n_u).
    n_u es el numero de nodos de los lados 0 y 2.
    n_v es el numero de nodos de los lados 1 y 3.
    """

    block_id: int
    grid: List[List[Point2D]]

    @property
    def n_u(self) -> int:
        return len(self.grid[0]) if self.grid else 0

    @property
    def n_v(self) -> int:
        return len(self.grid)

    def cell_count(self) -> int:
        if self.n_u < 2 or self.n_v < 2:
            return 0
        return (self.n_u - 1) * (self.n_v - 1)

    def point(self, i: int, j: int) -> Point2D:
        return self.grid[j][i]


def mesh_block(block: Block, topology: Topology, mesh_model: MeshModel) -> BlockMesh:
    """Genera la malla de un bloque usando sus 4 lados y el modelo de malla."""
    side_samples = [
        mesh_model.side_samples(side, topology) for side in block.sides
    ]
    s0, s1, s2, s3 = side_samples

    if len(s0) < 2 or len(s1) < 2 or len(s2) < 2 or len(s3) < 2:
        raise ValueError("Cada lado debe tener al menos 2 nodos")

    if len(s0) != len(s2):
        raise ValueError(
            "Lados 0 y 2 con distinto numero de nodos: {} vs {}".format(
                len(s0), len(s2)
            )
        )
    if len(s1) != len(s3):
        raise ValueError(
            "Lados 1 y 3 con distinto numero de nodos: {} vs {}".format(
                len(s1), len(s3)
            )
        )

    grid = tfi_grid(s0, s1, s2, s3)
    return BlockMesh(block_id=block.id, grid=grid)
'''

MESH_INIT_STEP31 = '''"""Generacion de malla estructurada y distribuciones de nodos."""

from meshcad.core.mesh.distribution import (
    BiasedDistribution,
    NodeDistribution,
    UniformDistribution,
)
from meshcad.core.mesh.model import EdgeMeshSpec, MeshModel, DEFAULT_N_NODES
from meshcad.core.mesh.tfi import tfi_grid
from meshcad.core.mesh.generator import BlockMesh, mesh_block

__all__ = [
    "NodeDistribution",
    "UniformDistribution",
    "BiasedDistribution",
    "EdgeMeshSpec",
    "MeshModel",
    "DEFAULT_N_NODES",
    "tfi_grid",
    "BlockMesh",
    "mesh_block",
]
'''

TEST_GENERATOR = '''import math

import pytest

from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.mesh.distribution import UniformDistribution
from meshcad.core.mesh.generator import BlockMesh, mesh_block
from meshcad.core.mesh.model import EdgeMeshSpec, MeshModel
from meshcad.core.topology.block import Block
from meshcad.core.topology.loop import Loop
from meshcad.core.topology.topology import Topology


def build_square_block(n_nodes=4):
    """Cuadrado [0,1]x[0,1] con 4 aristas y un bloque."""
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
    for e in (e0, e1, e2, e3):
        loop.add_edge(e.id)

    sides = loop.split_at_corners(t, [v0.id, v1.id, v2.id, v3.id])
    block = Block(0, sides)

    model = MeshModel()
    for e in (e0, e1, e2, e3):
        model.set_spec(EdgeMeshSpec(e.id, n_nodes, UniformDistribution()))
    return t, block, model, (v0, v1, v2, v3), (e0, e1, e2, e3)


def test_mesh_block_grid_size():
    t, block, model, _, _ = build_square_block(n_nodes=4)
    bm = mesh_block(block, t, model)
    assert bm.n_u == 4
    assert bm.n_v == 4
    assert bm.cell_count() == 9


def test_mesh_block_corners():
    t, block, model, (v0, v1, v2, v3), _ = build_square_block(n_nodes=4)
    bm = mesh_block(block, t, model)
    assert bm.point(0, 0) == Point2D(0, 0)
    assert bm.point(3, 0) == Point2D(1, 0)
    assert bm.point(3, 3) == Point2D(1, 1)
    assert bm.point(0, 3) == Point2D(0, 1)


def test_mesh_block_rectangle_uniform():
    t, block, model, _, _ = build_square_block(n_nodes=5)
    bm = mesh_block(block, t, model)
    for j in range(5):
        for i in range(5):
            assert math.isclose(bm.point(i, j).x, i / 4.0)
            assert math.isclose(bm.point(i, j).y, j / 4.0)


def test_mesh_block_requires_matching_opposite_sides():
    t, block, model, _, (e0, e1, e2, e3) = build_square_block(n_nodes=4)
    model.set_spec(EdgeMeshSpec(e0.id, 4, UniformDistribution()))
    model.set_spec(EdgeMeshSpec(e2.id, 6, UniformDistribution()))  # desajuste
    with pytest.raises(ValueError):
        mesh_block(block, t, model)


def test_mesh_block_with_different_counts_per_direction():
    t, block, model, _, (e0, e1, e2, e3) = build_square_block(n_nodes=4)
    model.set_spec(EdgeMeshSpec(e0.id, 5, UniformDistribution()))
    model.set_spec(EdgeMeshSpec(e2.id, 5, UniformDistribution()))
    model.set_spec(EdgeMeshSpec(e1.id, 7, UniformDistribution()))
    model.set_spec(EdgeMeshSpec(e3.id, 7, UniformDistribution()))
    bm = mesh_block(block, t, model)
    assert bm.n_u == 5
    assert bm.n_v == 7


def test_adjacent_blocks_are_conformal():
    """Dos cuadrados que comparten arista deben dar la misma linea de nodos."""
    t = Topology()
    # Cuadrado izquierdo
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    v2 = t.add_vertex(Point2D(1, 1))
    v3 = t.add_vertex(Point2D(0, 1))
    # Cuadrado derecho
    v4 = t.add_vertex(Point2D(2, 0))
    v5 = t.add_vertex(Point2D(2, 1))

    e_bottom_left = t.add_edge(v0, v1, Line(v0.point, v1.point))
    e_shared = t.add_edge(v1, v2, Line(v1.point, v2.point))       # compartida
    e_top_left = t.add_edge(v2, v3, Line(v2.point, v3.point))
    e_left = t.add_edge(v3, v0, Line(v3.point, v0.point))
    e_bottom_right = t.add_edge(v1, v4, Line(v1.point, v4.point))
    e_top_right = t.add_edge(v4, v5, Line(v4.point, v5.point))
    e_right = t.add_edge(v2, v5, Line(v2.point, v5.point))

    loop_left = Loop()
    loop_left.add_edge(e_bottom_left.id)
    loop_left.add_edge(e_shared.id)
    loop_left.add_edge(e_top_left.id, reversed=True)
    loop_left.add_edge(e_left.id, reversed=True)

    loop_right = Loop()
    loop_right.add_edge(e_bottom_right.id)
    loop_right.add_edge(e_top_right.id)
    loop_right.add_edge(e_right.id, reversed=True)
    loop_right.add_edge(e_shared.id, reversed=True)

    sides_left = loop_left.split_at_corners(t, [v0.id, v1.id, v2.id, v3.id])
    sides_right = loop_right.split_at_corners(t, [v1.id, v4.id, v5.id, v2.id])
    block_left = Block(0, sides_left)
    block_right = Block(1, sides_right)

    model = MeshModel()
    n_nodes = 5
    for e in (e_bottom_left, e_shared, e_top_left, e_left,
              e_bottom_right, e_top_right, e_right):
        model.set_spec(EdgeMeshSpec(e.id, n_nodes, UniformDistribution()))

    bm_left = mesh_block(block_left, t, model)
    bm_right = mesh_block(block_right, t, model)

    # El lado este del bloque izquierdo es la columna n_u-1
    left_edge_points = [
        (round(bm_left.point(bm_left.n_u - 1, j).x, 9),
         round(bm_left.point(bm_left.n_u - 1, j).y, 9))
        for j in range(bm_left.n_v)
    ]
    # El lado oeste del bloque derecho es la columna 0
    right_edge_points = [
        (round(bm_right.point(0, j).x, 9),
         round(bm_right.point(0, j).y, 9))
        for j in range(bm_right.n_v)
    ]

    # Los conjuntos de puntos deben coincidir (aunque el orden se invierta)
    assert set(left_edge_points) == set(right_edge_points)
'''


# =========================================================================== #
# COMMIT 32 - Document.generate_mesh
# =========================================================================== #

DOCUMENT_PY = '''"""Documento: estado del proyecto (topologia, malla y bloques)."""

from __future__ import annotations

from typing import List

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QUndoStack

from meshcad.core.mesh.generator import BlockMesh, mesh_block
from meshcad.core.mesh.model import EdgeMeshSpec, MeshModel
from meshcad.core.topology.block import Block
from meshcad.core.topology.topology import Topology


class Document(QObject):
    """Estado del proyecto."""

    topology_changed = pyqtSignal()
    mesh_changed = pyqtSignal()
    blocks_changed = pyqtSignal()
    mesh_generated = pyqtSignal()

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

    def generate_mesh(self) -> List[BlockMesh]:
        """Genera la malla de todos los bloques del documento."""
        self.block_meshes = []
        errors = []
        for block in self.blocks:
            try:
                bm = mesh_block(block, self.topology, self.mesh)
            except ValueError as e:
                errors.append("Bloque {}: {}".format(block.id, e))
                continue
            self.block_meshes.append(bm)
        self.mesh_generated.emit()
        return self.block_meshes, errors
'''

TEST_DOCUMENT = '''import math

from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.mesh.distribution import UniformDistribution
from meshcad.core.mesh.model import EdgeMeshSpec
from meshcad.core.topology.block import Block
from meshcad.core.topology.loop import Loop
from meshcad.core.topology.topology import Topology
from meshcad.gui.document import Document


def build_square_block(doc, n_nodes=4):
    t = doc.topology
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    v2 = t.add_vertex(Point2D(1, 1))
    v3 = t.add_vertex(Point2D(0, 1))
    e0 = t.add_edge(v0, v1, Line(v0.point, v1.point))
    e1 = t.add_edge(v1, v2, Line(v1.point, v2.point))
    e2 = t.add_edge(v2, v3, Line(v2.point, v3.point))
    e3 = t.add_edge(v3, v0, Line(v3.point, v0.point))

    loop = Loop()
    for e in (e0, e1, e2, e3):
        loop.add_edge(e.id)

    sides = loop.split_at_corners(t, [v0.id, v1.id, v2.id, v3.id])
    block = Block(doc.next_block_id(), sides)
    doc.add_block(block)

    for e in (e0, e1, e2, e3):
        doc.set_edge_spec(EdgeMeshSpec(e.id, n_nodes, UniformDistribution()))
    return block


def test_generate_mesh_no_blocks(qtbot):
    doc = Document()
    meshes, errors = doc.generate_mesh()
    assert meshes == []
    assert errors == []


def test_generate_mesh_single_block(qtbot):
    doc = Document()
    build_square_block(doc, n_nodes=5)
    meshes, errors = doc.generate_mesh()
    assert len(meshes) == 1
    assert errors == []
    assert meshes[0].n_u == 5
    assert meshes[0].n_v == 5


def test_generate_mesh_emits_signal(qtbot):
    doc = Document()
    build_square_block(doc, n_nodes=4)
    with qtbot.waitSignal(doc.mesh_generated, timeout=1000):
        doc.generate_mesh()


def test_generate_mesh_reports_mismatch(qtbot):
    doc = Document()
    t = doc.topology
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    v2 = t.add_vertex(Point2D(1, 1))
    v3 = t.add_vertex(Point2D(0, 1))
    e0 = t.add_edge(v0, v1, Line(v0.point, v1.point))
    e1 = t.add_edge(v1, v2, Line(v1.point, v2.point))
    e2 = t.add_edge(v2, v3, Line(v2.point, v3.point))
    e3 = t.add_edge(v3, v0, Line(v3.point, v0.point))

    loop = Loop()
    for e in (e0, e1, e2, e3):
        loop.add_edge(e.id)
    sides = loop.split_at_corners(t, [v0.id, v1.id, v2.id, v3.id])
    doc.add_block(Block(doc.next_block_id(), sides))

    # Desajuste lados 0/2
    doc.set_edge_spec(EdgeMeshSpec(e0.id, 4, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(e2.id, 6, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(e1.id, 4, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(e3.id, 4, UniformDistribution()))

    meshes, errors = doc.generate_mesh()
    assert meshes == []
    assert len(errors) == 1
    assert "Bloque 0" in errors[0]
'''


# =========================================================================== #
# COMMIT 33 - GUI: boton y renderizado
# =========================================================================== #

CANVAS_PY = '''"""Lienzo CAD interactivo basado en QGraphicsView."""

from __future__ import annotations

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsPathItem,
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
        self._mesh_item = None

        self.document.topology_changed.connect(self._redraw_vertices)
        self.document.mesh_generated.connect(self._on_mesh_generated)

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

    # ------------------------------ mesh --------------------------------- #

    def show_mesh(self, block_meshes) -> None:
        """Dibuja las mallas de los bloques como lineas finas."""
        self.clear_mesh()
        path = QPainterPath()
        for bm in block_meshes:
            grid = bm.grid
            n_v = len(grid)
            if n_v == 0:
                continue
            n_u = len(grid[0])

            # Lineas verticales (columnas)
            for i in range(n_u):
                path.moveTo(grid[0][i].x, grid[0][i].y)
                for j in range(1, n_v):
                    path.lineTo(grid[j][i].x, grid[j][i].y)
            # Lineas horizontales (filas)
            for j in range(n_v):
                path.moveTo(grid[j][0].x, grid[j][0].y)
                for i in range(1, n_u):
                    path.lineTo(grid[j][i].x, grid[j][i].y)

        item = QGraphicsPathItem(path)
        pen = QPen(QColor(40, 40, 40))
        pen.setWidthF(0.8)
        pen.setCosmetic(True)
        item.setPen(pen)
        item.setZValue(3.0)
        self.scene().addItem(item)
        self._mesh_item = item

    def clear_mesh(self) -> None:
        if self._mesh_item is not None:
            self.scene().removeItem(self._mesh_item)
            self._mesh_item = None

    def _on_mesh_generated(self) -> None:
        self.show_mesh(self.document.block_meshes)

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

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QLabel,
    QMainWindow,
    QStatusBar,
    QToolBar,
)

from meshcad.gui.blocks_panel import BlocksPanel
from meshcad.gui.canvas import CadCanvas
from meshcad.gui.document import Document
from meshcad.gui.edges_panel import EdgesPanel
from meshcad.gui.loops_panel import LoopsPanel
from meshcad.gui.tools.arc_tool import ArcTool
from meshcad.gui.tools.line_tool import LineTool
from meshcad.gui.tools.spline_tool import SplineTool


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MeshCAD")
        self.resize(1400, 800)

        self.document = Document()
        self.canvas = CadCanvas(self.document)
        self.setCentralWidget(self.canvas)

        self.loops_panel = LoopsPanel(self.document, self.canvas, self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.loops_panel)

        self.edges_panel = EdgesPanel(self.document, self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.edges_panel)

        self.blocks_panel = BlocksPanel(self.document, self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.blocks_panel)

        self.document.topology_changed.connect(self.edges_panel.refresh)
        self.document.mesh_generated.connect(self._on_mesh_generated)

        status = QStatusBar()
        self.setStatusBar(status)
        self.status_label = QLabel("Listo")
        status.addWidget(self.status_label)

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

        toolbar.addSeparator()

        self.action_mesh = QAction("Generar malla", self)
        self.action_mesh.triggered.connect(self._on_generate_mesh)
        toolbar.addAction(self.action_mesh)

        self.action_clear_mesh = QAction("Borrar malla", self)
        self.action_clear_mesh.triggered.connect(self.canvas.clear_mesh)
        toolbar.addAction(self.action_clear_mesh)

    def _on_generate_mesh(self) -> None:
        meshes, errors = self.document.generate_mesh()
        if errors:
            self.status_label.setText(
                "Errores: " + "; ".join(errors)
            )
        else:
            total_cells = sum(bm.cell_count() for bm in meshes)
            self.status_label.setText(
                "Malla generada: {} bloques, {} celdas".format(
                    len(meshes), total_cells
                )
            )

    def _on_mesh_generated(self) -> None:
        pass


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
'''

TEST_CANVAS_MESH = '''from PyQt5.QtGui import QPainterPath
from PyQt5.QtWidgets import QGraphicsPathItem

from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.mesh.distribution import UniformDistribution
from meshcad.core.mesh.model import EdgeMeshSpec
from meshcad.core.topology.block import Block
from meshcad.core.topology.loop import Loop
from meshcad.gui.canvas import CadCanvas
from meshcad.gui.document import Document


def build_square(doc, n_nodes=4):
    t = doc.topology
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    v2 = t.add_vertex(Point2D(1, 1))
    v3 = t.add_vertex(Point2D(0, 1))
    e0 = t.add_edge(v0, v1, Line(v0.point, v1.point))
    e1 = t.add_edge(v1, v2, Line(v1.point, v2.point))
    e2 = t.add_edge(v2, v3, Line(v2.point, v3.point))
    e3 = t.add_edge(v3, v0, Line(v3.point, v0.point))
    loop = Loop()
    for e in (e0, e1, e2, e3):
        loop.add_edge(e.id)
    sides = loop.split_at_corners(t, [v0.id, v1.id, v2.id, v3.id])
    doc.add_block(Block(doc.next_block_id(), sides))
    for e in (e0, e1, e2, e3):
        doc.set_edge_spec(EdgeMeshSpec(e.id, n_nodes, UniformDistribution()))


def test_canvas_draws_mesh(qtbot):
    doc = Document()
    canvas = CadCanvas(doc)
    qtbot.addWidget(canvas)
    build_square(doc, n_nodes=4)

    assert canvas._mesh_item is None
    doc.generate_mesh()
    assert canvas._mesh_item is not None
    assert isinstance(canvas._mesh_item, QGraphicsPathItem)


def test_canvas_clear_mesh(qtbot):
    doc = Document()
    canvas = CadCanvas(doc)
    qtbot.addWidget(canvas)
    build_square(doc, n_nodes=4)
    doc.generate_mesh()
    assert canvas._mesh_item is not None
    canvas.clear_mesh()
    assert canvas._mesh_item is None
'''


# =========================================================================== #
# Ejecucion
# =========================================================================== #

def main():
    check()

    commit(
        "Commit 30/33: TFI",
        {
            "src/meshcad/core/mesh/tfi.py": TFI_PY,
            "src/meshcad/core/mesh/__init__.py": MESH_INIT_STEP30,
            "tests/core/mesh/test_tfi.py": TEST_TFI,
        },
        "feat(core): interpolacion transfinita (TFI) para cuadrilateros",
    )

    commit(
        "Commit 31/33: Generador de malla",
        {
            "src/meshcad/core/mesh/generator.py": GENERATOR_PY,
            "src/meshcad/core/mesh/__init__.py": MESH_INIT_STEP31,
            "tests/core/mesh/test_generator.py": TEST_GENERATOR,
        },
        "feat(core): BlockMesh y generacion de malla por bloque",
    )

    commit(
        "Commit 32/33: Document.generate_mesh",
        {
            "src/meshcad/gui/document.py": DOCUMENT_PY,
            "tests/gui/test_document.py": TEST_DOCUMENT,
        },
        "feat(gui): Document.generate_mesh y senal mesh_generated",
    )

    commit(
        "Commit 33/33: Boton y renderizado de malla",
        {
            "src/meshcad/gui/canvas.py": CANVAS_PY,
            "src/meshcad/gui/main_window.py": MAIN_WINDOW_PY,
            "tests/gui/test_canvas_mesh.py": TEST_CANVAS_MESH,
        },
        "feat(gui): boton generar malla y renderizado de la rejilla",
    )

    print()
    print("== Verificando todos los tests ==")
    run([sys.executable, "-m", "pytest", "-q"])

    print()
    print("== Historial ==")
    run(["git", "log", "--oneline", "--decorate"])

    print()
    print("Fase 6 completada. Ejecuta 'python -m meshcad'.")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print()
        print("ERROR:", e)
        sys.exit(1)