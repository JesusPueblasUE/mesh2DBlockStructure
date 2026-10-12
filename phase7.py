#!/usr/bin/env python3
"""
Fase 7 del proyecto MeshCAD: persistencia y exportacion.

Crea los commits atomicos de la fase 7:
serializacion JSON, save/load, menu Archivo y exportacion VTK.

Uso:
    cd meshcad
    python phase7.py
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
# COMMIT 34 - Serializacion de geometria y distribuciones
# =========================================================================== #

JSON_IO_PY = '''"""Serializacion JSON de geometria, topologia, malla y bloques."""

from __future__ import annotations

from typing import Any, Dict, List

from meshcad.core.geometry.arc import Arc
from meshcad.core.geometry.entity import GeometryEntity
from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.geometry.spline import Spline
from meshcad.core.mesh.distribution import (
    BiasedDistribution,
    NodeDistribution,
    UniformDistribution,
)


# ------------------------------- helpers ------------------------------- #


def _point_to_list(p: Point2D) -> List[float]:
    return [p.x, p.y]


def _point_from_list(data) -> Point2D:
    return Point2D(float(data[0]), float(data[1]))


# ------------------------------ geometria ------------------------------ #


def geometry_to_dict(g: GeometryEntity) -> Dict[str, Any]:
    if isinstance(g, Line):
        return {
            "type": "line",
            "start": _point_to_list(g.start),
            "end": _point_to_list(g.end),
        }
    if isinstance(g, Arc):
        return {
            "type": "arc",
            "center": _point_to_list(g.center),
            "radius": g.radius,
            "start_angle": g.start_angle,
            "end_angle": g.end_angle,
        }
    if isinstance(g, Spline):
        return {
            "type": "spline",
            "points": [_point_to_list(p) for p in g.points],
        }
    raise TypeError("Tipo de geometria no serializable: {}".format(type(g).__name__))


def geometry_from_dict(data: Dict[str, Any]) -> GeometryEntity:
    t = data.get("type")
    if t == "line":
        return Line(_point_from_list(data["start"]), _point_from_list(data["end"]))
    if t == "arc":
        return Arc(
            _point_from_list(data["center"]),
            float(data["radius"]),
            float(data["start_angle"]),
            float(data["end_angle"]),
        )
    if t == "spline":
        pts = tuple(_point_from_list(p) for p in data["points"])
        return Spline(pts)
    raise ValueError("Tipo de geometria desconocido: {!r}".format(t))


# --------------------------- distribuciones ---------------------------- #


def distribution_to_dict(d: NodeDistribution) -> Dict[str, Any]:
    if isinstance(d, UniformDistribution):
        return {"type": "uniform"}
    if isinstance(d, BiasedDistribution):
        return {
            "type": "biased",
            "bias": d.bias,
            "from_start": d.from_start,
        }
    raise TypeError("Distribucion no serializable: {}".format(type(d).__name__))


def distribution_from_dict(data: Dict[str, Any]) -> NodeDistribution:
    t = data.get("type")
    if t == "uniform":
        return UniformDistribution()
    if t == "biased":
        return BiasedDistribution(
            bias=float(data["bias"]),
            from_start=bool(data.get("from_start", True)),
        )
    raise ValueError("Distribucion desconocida: {!r}".format(t))
'''

TEST_JSON_GEOM = '''import math

import pytest

from meshcad.core.geometry.arc import Arc
from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.geometry.spline import Spline
from meshcad.core.mesh.distribution import (
    BiasedDistribution,
    UniformDistribution,
)
from meshcad.io.json_io import (
    distribution_from_dict,
    distribution_to_dict,
    geometry_from_dict,
    geometry_to_dict,
)


def test_line_round_trip():
    line = Line(Point2D(1.0, 2.0), Point2D(3.5, -4.0))
    data = geometry_to_dict(line)
    assert data["type"] == "line"
    back = geometry_from_dict(data)
    assert back == line


def test_arc_round_trip():
    arc = Arc(Point2D(0, 0), 2.5, 0.1, math.pi / 3)
    data = geometry_to_dict(arc)
    assert data["type"] == "arc"
    back = geometry_from_dict(data)
    assert math.isclose(back.radius, arc.radius)
    assert math.isclose(back.start_angle, arc.start_angle)
    assert math.isclose(back.end_angle, arc.end_angle)
    assert back.center == arc.center


def test_spline_round_trip():
    pts = (Point2D(0, 0), Point2D(1, 2), Point2D(2.5, -1), Point2D(4, 0))
    sp = Spline(pts)
    data = geometry_to_dict(sp)
    assert data["type"] == "spline"
    back = geometry_from_dict(data)
    assert back.points == pts


def test_geometry_type_discriminator_required():
    with pytest.raises(ValueError):
        geometry_from_dict({"foo": "bar"})


def test_uniform_round_trip():
    d = UniformDistribution()
    data = distribution_to_dict(d)
    assert data == {"type": "uniform"}
    back = distribution_from_dict(data)
    assert isinstance(back, UniformDistribution)


def test_biased_round_trip():
    d = BiasedDistribution(bias=1.7, from_start=False)
    data = distribution_to_dict(d)
    back = distribution_from_dict(data)
    assert isinstance(back, BiasedDistribution)
    assert math.isclose(back.bias, 1.7)
    assert back.from_start is False


def test_unknown_distribution_raises():
    with pytest.raises(ValueError):
        distribution_from_dict({"type": "unknown"})
'''

IO_INIT_STEP34 = '''"""Persistencia (JSON) y exportacion (VTK)."""

from meshcad.io.json_io import (
    distribution_from_dict,
    distribution_to_dict,
    geometry_from_dict,
    geometry_to_dict,
)

__all__ = [
    "geometry_to_dict",
    "geometry_from_dict",
    "distribution_to_dict",
    "distribution_from_dict",
]
'''


# =========================================================================== #
# COMMIT 35 - Serializacion de topologia, malla y bloques
# =========================================================================== #

TOPOLOGY_LOAD_PATCH = '''    def _load_state(self, vertices, edges) -> None:
        """Reemplaza el estado interno (uso: deserializacion)."""
        from itertools import count as _count

        self._vertices = dict(vertices)
        self._edges = dict(edges)
        max_v = max(self._vertices.keys(), default=-1)
        max_e = max(self._edges.keys(), default=-1)
        self._vertex_ids = _count(max_v + 1)
        self._edge_ids = _count(max_e + 1)
'''

JSON_IO_FULL = '''"""Serializacion JSON de geometria, topologia, malla y bloques."""

from __future__ import annotations

from typing import Any, Dict, List

from meshcad.core.geometry.arc import Arc
from meshcad.core.geometry.entity import GeometryEntity
from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.geometry.spline import Spline
from meshcad.core.mesh.distribution import (
    BiasedDistribution,
    NodeDistribution,
    UniformDistribution,
)
from meshcad.core.mesh.model import EdgeMeshSpec
from meshcad.core.topology.block import Block
from meshcad.core.topology.block_side import BlockSide
from meshcad.core.topology.edge import Edge, OrientedEdge
from meshcad.core.topology.topology import Topology
from meshcad.core.topology.vertex import Vertex


# ------------------------------- helpers ------------------------------- #


def _point_to_list(p: Point2D) -> List[float]:
    return [p.x, p.y]


def _point_from_list(data) -> Point2D:
    return Point2D(float(data[0]), float(data[1]))


# ------------------------------ geometria ------------------------------ #


def geometry_to_dict(g: GeometryEntity) -> Dict[str, Any]:
    if isinstance(g, Line):
        return {
            "type": "line",
            "start": _point_to_list(g.start),
            "end": _point_to_list(g.end),
        }
    if isinstance(g, Arc):
        return {
            "type": "arc",
            "center": _point_to_list(g.center),
            "radius": g.radius,
            "start_angle": g.start_angle,
            "end_angle": g.end_angle,
        }
    if isinstance(g, Spline):
        return {
            "type": "spline",
            "points": [_point_to_list(p) for p in g.points],
        }
    raise TypeError("Tipo de geometria no serializable: {}".format(type(g).__name__))


def geometry_from_dict(data: Dict[str, Any]) -> GeometryEntity:
    t = data.get("type")
    if t == "line":
        return Line(_point_from_list(data["start"]), _point_from_list(data["end"]))
    if t == "arc":
        return Arc(
            _point_from_list(data["center"]),
            float(data["radius"]),
            float(data["start_angle"]),
            float(data["end_angle"]),
        )
    if t == "spline":
        pts = tuple(_point_from_list(p) for p in data["points"])
        return Spline(pts)
    raise ValueError("Tipo de geometria desconocido: {!r}".format(t))


# --------------------------- distribuciones ---------------------------- #


def distribution_to_dict(d: NodeDistribution) -> Dict[str, Any]:
    if isinstance(d, UniformDistribution):
        return {"type": "uniform"}
    if isinstance(d, BiasedDistribution):
        return {
            "type": "biased",
            "bias": d.bias,
            "from_start": d.from_start,
        }
    raise TypeError("Distribucion no serializable: {}".format(type(d).__name__))


def distribution_from_dict(data: Dict[str, Any]) -> NodeDistribution:
    t = data.get("type")
    if t == "uniform":
        return UniformDistribution()
    if t == "biased":
        return BiasedDistribution(
            bias=float(data["bias"]),
            from_start=bool(data.get("from_start", True)),
        )
    raise ValueError("Distribucion desconocida: {!r}".format(t))


# ------------------------------ topologia ------------------------------ #


def topology_to_dict(t: Topology) -> Dict[str, Any]:
    return {
        "vertices": [
            {"id": v.id, "point": _point_to_list(v.point)} for v in t.vertices()
        ],
        "edges": [
            {
                "id": e.id,
                "start_vertex_id": e.start_vertex_id,
                "end_vertex_id": e.end_vertex_id,
                "geometry": geometry_to_dict(e.geometry),
            }
            for e in t.edges()
        ],
    }


def topology_from_dict(data: Dict[str, Any]) -> Topology:
    t = Topology()
    vertices: Dict[int, Vertex] = {}
    for vd in data.get("vertices", []):
        v = Vertex(int(vd["id"]), _point_from_list(vd["point"]))
        vertices[v.id] = v
    edges: Dict[int, Edge] = {}
    for ed in data.get("edges", []):
        g = geometry_from_dict(ed["geometry"])
        e = Edge(
            int(ed["id"]),
            int(ed["start_vertex_id"]),
            int(ed["end_vertex_id"]),
            g,
        )
        edges[e.id] = e
    t._load_state(vertices, edges)
    return t


# --------------------------- malla por arista -------------------------- #


def edge_spec_to_dict(spec: EdgeMeshSpec) -> Dict[str, Any]:
    return {
        "edge_id": spec.edge_id,
        "n_nodes": spec.n_nodes,
        "distribution": distribution_to_dict(spec.distribution),
    }


def edge_spec_from_dict(data: Dict[str, Any]) -> EdgeMeshSpec:
    return EdgeMeshSpec(
        int(data["edge_id"]),
        int(data["n_nodes"]),
        distribution_from_dict(data["distribution"]),
    )


# ------------------------------ bloques -------------------------------- #


def block_side_to_dict(side: BlockSide) -> Dict[str, Any]:
    return {
        "oriented_edges": [
            {"edge_id": oe.edge_id, "reversed": oe.reversed}
            for oe in side.oriented_edges
        ],
        "node_count": side.node_count,
    }


def block_side_from_dict(data: Dict[str, Any]) -> BlockSide:
    oriented = tuple(
        OrientedEdge(int(oe["edge_id"]), bool(oe.get("reversed", False)))
        for oe in data["oriented_edges"]
    )
    return BlockSide(oriented_edges=oriented, node_count=int(data.get("node_count", 0)))


def block_to_dict(block: Block) -> Dict[str, Any]:
    return {
        "id": block.id,
        "sides": [block_side_to_dict(s) for s in block.sides],
    }


def block_from_dict(data: Dict[str, Any]) -> Block:
    sides = tuple(block_side_from_dict(sd) for sd in data["sides"])
    if len(sides) != 4:
        raise ValueError(
            "El bloque {} no tiene 4 lados en el fichero".format(data.get("id"))
        )
    return Block(int(data["id"]), sides)  # type: ignore[arg-type]
'''

IO_INIT_STEP35 = '''"""Persistencia (JSON) y exportacion (VTK)."""

from meshcad.io.json_io import (
    block_from_dict,
    block_side_from_dict,
    block_side_to_dict,
    block_to_dict,
    distribution_from_dict,
    distribution_to_dict,
    edge_spec_from_dict,
    edge_spec_to_dict,
    geometry_from_dict,
    geometry_to_dict,
    topology_from_dict,
    topology_to_dict,
)

__all__ = [
    "geometry_to_dict",
    "geometry_from_dict",
    "distribution_to_dict",
    "distribution_from_dict",
    "topology_to_dict",
    "topology_from_dict",
    "edge_spec_to_dict",
    "edge_spec_from_dict",
    "block_side_to_dict",
    "block_side_from_dict",
    "block_to_dict",
    "block_from_dict",
]
'''

TEST_JSON_TOPOLOGY = '''import math

import pytest

from meshcad.core.geometry.arc import Arc
from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.mesh.distribution import BiasedDistribution, UniformDistribution
from meshcad.core.mesh.model import EdgeMeshSpec
from meshcad.core.topology.block import Block
from meshcad.core.topology.block_side import BlockSide
from meshcad.core.topology.edge import OrientedEdge
from meshcad.core.topology.loop import Loop
from meshcad.core.topology.topology import Topology
from meshcad.io.json_io import (
    block_from_dict,
    block_to_dict,
    edge_spec_from_dict,
    edge_spec_to_dict,
    topology_from_dict,
    topology_to_dict,
)


def make_square_topology():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    v2 = t.add_vertex(Point2D(1, 1))
    v3 = t.add_vertex(Point2D(0, 1))
    t.add_edge(v0, v1, Line(v0.point, v1.point))
    t.add_edge(v1, v2, Line(v1.point, v2.point))
    t.add_edge(v2, v3, Arc(Point2D(0.5, 0.5), 0.5, math.pi / 2, math.pi))
    t.add_edge(v3, v0, Line(v3.point, v0.point))
    return t


def test_topology_round_trip_preserves_ids():
    t = make_square_topology()
    data = topology_to_dict(t)
    back = topology_from_dict(data)
    assert sorted(v.id for v in back.vertices()) == sorted(
        v.id for v in t.vertices()
    )
    assert sorted(e.id for e in back.edges()) == sorted(e.id for e in t.edges())


def test_topology_round_trip_preserves_geometry():
    t = make_square_topology()
    back = topology_from_dict(topology_to_dict(t))
    for e in t.edges():
        be = back.get_edge(e.id)
        assert isinstance(be.geometry, type(e.geometry))
        assert be.start_vertex_id == e.start_vertex_id
        assert be.end_vertex_id == e.end_vertex_id


def test_topology_counter_continues_after_load():
    t = make_square_topology()
    back = topology_from_dict(topology_to_dict(t))
    v_new = back.add_vertex(Point2D(10, 10))
    v_last_id = max(v.id for v in t.vertices())
    assert v_new.id == v_last_id + 1


def test_edge_spec_round_trip():
    spec = EdgeMeshSpec(3, 7, BiasedDistribution(bias=1.5))
    data = edge_spec_to_dict(spec)
    back = edge_spec_from_dict(data)
    assert back.edge_id == 3
    assert back.n_nodes == 7
    assert isinstance(back.distribution, BiasedDistribution)
    assert math.isclose(back.distribution.bias, 1.5)


def test_block_round_trip():
    sides = (
        BlockSide((OrientedEdge(0),), node_count=4),
        BlockSide((OrientedEdge(1, reversed=True),), node_count=5),
        BlockSide((OrientedEdge(2),), node_count=4),
        BlockSide((OrientedEdge(3, reversed=True),), node_count=5),
    )
    block = Block(7, sides)
    data = block_to_dict(block)
    back = block_from_dict(data)
    assert back.id == 7
    assert back.sides[0].edge_ids() == [0]
    assert back.sides[1].oriented_edges[0].reversed is True
    assert back.sides[2].node_count == 4
    back.validate_opposite_sides()


def test_block_from_dict_rejects_wrong_sides():
    with pytest.raises(ValueError):
        block_from_dict({"id": 0, "sides": []})
'''


# =========================================================================== #
# COMMIT 36 - Document.save / load
# =========================================================================== #

DOCUMENT_PY = '''"""Documento: estado del proyecto (topologia, malla y bloques)."""

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
'''

JSON_IO_SAVE = '''"""Persistencia (JSON) y exportacion (VTK)."""

from meshcad.io.json_io import (
    block_from_dict,
    block_side_from_dict,
    block_side_to_dict,
    block_to_dict,
    distribution_from_dict,
    distribution_to_dict,
    edge_spec_from_dict,
    edge_spec_to_dict,
    geometry_from_dict,
    geometry_to_dict,
    topology_from_dict,
    topology_to_dict,
)
from meshcad.io.project_io import load_project, save_project

__all__ = [
    "geometry_to_dict",
    "geometry_from_dict",
    "distribution_to_dict",
    "distribution_from_dict",
    "topology_to_dict",
    "topology_from_dict",
    "edge_spec_to_dict",
    "edge_spec_from_dict",
    "block_side_to_dict",
    "block_side_from_dict",
    "block_to_dict",
    "block_from_dict",
    "save_project",
    "load_project",
]
'''

PROJECT_IO_PY = '''"""Guardar y cargar proyectos en formato JSON."""

from __future__ import annotations

import json
from pathlib import Path

from meshcad.gui.document import Document


def save_project(document: Document, path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = document.to_dict()
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_project(path) -> Document:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return Document.from_dict(data)
'''

TEST_PROJECT_IO = '''import math

from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.mesh.distribution import BiasedDistribution, UniformDistribution
from meshcad.core.mesh.model import EdgeMeshSpec
from meshcad.core.topology.block import Block
from meshcad.core.topology.loop import Loop
from meshcad.core.topology.topology import Topology
from meshcad.gui.document import Document
from meshcad.io.project_io import load_project, save_project


def build_document():
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

    doc.set_edge_spec(EdgeMeshSpec(e0.id, 4, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(e1.id, 5, BiasedDistribution(bias=1.5)))
    doc.set_edge_spec(EdgeMeshSpec(e2.id, 4, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(e3.id, 5, BiasedDistribution(bias=1.5)))
    return doc


def test_save_creates_file(tmp_path):
    doc = build_document()
    path = tmp_path / "proj.json"
    save_project(doc, path)
    assert path.exists()
    assert "meshcad-project" in path.read_text(encoding="utf-8")


def test_round_trip_topology(tmp_path):
    doc = build_document()
    path = tmp_path / "proj.json"
    save_project(doc, path)
    back = load_project(path)
    assert len(back.topology.vertices()) == 4
    assert len(back.topology.edges()) == 4
    for e in doc.topology.edges():
        be = back.topology.get_edge(e.id)
        assert be.start_vertex_id == e.start_vertex_id
        assert be.end_vertex_id == e.end_vertex_id


def test_round_trip_edge_specs(tmp_path):
    doc = build_document()
    path = tmp_path / "proj.json"
    save_project(doc, path)
    back = load_project(path)
    assert set(back.mesh.edge_specs.keys()) == set(doc.mesh.edge_specs.keys())
    for eid, spec in doc.mesh.edge_specs.items():
        bspec = back.mesh.get_spec(eid)
        assert bspec.n_nodes == spec.n_nodes
        assert type(bspec.distribution) is type(spec.distribution)
        if isinstance(spec.distribution, BiasedDistribution):
            assert math.isclose(
                bspec.distribution.bias, spec.distribution.bias
            )


def test_round_trip_blocks(tmp_path):
    doc = build_document()
    path = tmp_path / "proj.json"
    save_project(doc, path)
    back = load_project(path)
    assert len(back.blocks) == 1
    assert back.blocks[0].id == 0
    assert back.blocks[0].sides[0].edge_ids() == [0]
    back.blocks[0].validate_opposite_sides()


def test_generate_mesh_after_load(tmp_path):
    doc = build_document()
    path = tmp_path / "proj.json"
    save_project(doc, path)
    back = load_project(path)
    meshes, errors = back.generate_mesh()
    assert errors == []
    assert len(meshes) == 1
    assert meshes[0].n_u == 4
    assert meshes[0].n_v == 5


def test_next_block_id_survives(tmp_path):
    doc = build_document()
    # consumimos algunos IDs
    doc.next_block_id()
    doc.next_block_id()
    path = tmp_path / "proj.json"
    save_project(doc, path)
    back = load_project(path)
    assert back.next_block_id() >= 3


def test_load_from_replaces_state(qtbot):
    doc_a = Document()
    doc_b = build_document()
    assert len(doc_a.topology.vertices()) == 0
    with qtbot.waitSignal(doc_a.project_replaced, timeout=1000):
        doc_a.load_from(doc_b)
    assert len(doc_a.topology.vertices()) == 4
    assert len(doc_a.blocks) == 1
'''


# =========================================================================== #
# COMMIT 37 - Menu Archivo
# =========================================================================== #

MAIN_WINDOW_PY = '''"""Ventana principal de MeshCAD."""

import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
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
from meshcad.io.project_io import load_project, save_project


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MeshCAD - sin titulo")
        self.resize(1400, 800)

        self.document = Document()
        self.current_path = None

        self.canvas = CadCanvas(self.document)
        self.setCentralWidget(self.canvas)

        self.loops_panel = LoopsPanel(self.document, self.canvas, self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.loops_panel)

        self.edges_panel = EdgesPanel(self.document, self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.edges_panel)

        self.blocks_panel = BlocksPanel(self.document, self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.blocks_panel)

        self.document.topology_changed.connect(self.edges_panel.refresh)
        self.document.project_replaced.connect(self._on_project_replaced)

        status = QStatusBar()
        self.setStatusBar(status)
        self.status_label = QLabel("Listo")
        status.addWidget(self.status_label)

        self._create_menus()
        self._create_toolbar()

    # ------------------------------ menus ------------------------------- #

    def _create_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&Archivo")

        self.action_new = QAction("Nuevo", self)
        self.action_new.setShortcut("Ctrl+N")
        self.action_new.triggered.connect(self._on_new)
        file_menu.addAction(self.action_new)

        self.action_open = QAction("Abrir...", self)
        self.action_open.setShortcut("Ctrl+O")
        self.action_open.triggered.connect(self._on_open)
        file_menu.addAction(self.action_open)

        file_menu.addSeparator()

        self.action_save = QAction("Guardar", self)
        self.action_save.setShortcut("Ctrl+S")
        self.action_save.triggered.connect(self._on_save)
        file_menu.addAction(self.action_save)

        self.action_save_as = QAction("Guardar como...", self)
        self.action_save_as.setShortcut("Ctrl+Shift+S")
        self.action_save_as.triggered.connect(self._on_save_as)
        file_menu.addAction(self.action_save_as)

        file_menu.addSeparator()

        self.action_export_vtk = QAction("Exportar malla (VTK)...", self)
        self.action_export_vtk.triggered.connect(self._on_export_vtk)
        file_menu.addAction(self.action_export_vtk)

        file_menu.addSeparator()

        self.action_quit = QAction("Salir", self)
        self.action_quit.setShortcut("Ctrl+Q")
        self.action_quit.triggered.connect(self.close)
        file_menu.addAction(self.action_quit)

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

    # ---------------------------- file slots ---------------------------- #

    def _on_new(self) -> None:
        self.document.load_from(Document())
        self.current_path = None
        self.canvas.clear_mesh()
        self.canvas.clear_highlight()
        self._update_title()
        self.status_label.setText("Proyecto nuevo.")

    def _on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir proyecto", "", "MeshCAD (*.json);;Todos (*)"
        )
        if not path:
            return
        try:
            loaded = load_project(path)
        except Exception as e:
            QMessageBox.critical(self, "Error al abrir", str(e))
            return
        self.document.load_from(loaded)
        self.current_path = Path(path)
        self.canvas.clear_mesh()
        self._update_title()
        self.status_label.setText("Proyecto cargado: {}".format(path))

    def _on_save(self) -> None:
        if self.current_path is None:
            self._on_save_as()
            return
        self._save_to(self.current_path)

    def _on_save_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar proyecto como", "proyecto.json",
            "MeshCAD (*.json);;Todos (*)"
        )
        if not path:
            return
        self._save_to(Path(path))

    def _save_to(self, path: Path) -> None:
        try:
            save_project(self.document, path)
        except Exception as e:
            QMessageBox.critical(self, "Error al guardar", str(e))
            return
        self.current_path = path
        self._update_title()
        self.status_label.setText("Guardado en: {}".format(path))

    def _on_export_vtk(self) -> None:
        if not self.document.block_meshes:
            QMessageBox.information(
                self, "Sin malla",
                "Genera primero la malla con el boton 'Generar malla'."
            )
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar malla VTK", "malla.pvd",
            "ParaView Data (*.pvd);;Todos (*)"
        )
        if not path:
            return
        try:
            from meshcad.io.vtk_io import export_mesh_vtk
            export_mesh_vtk(self.document.block_meshes, path)
        except Exception as e:
            QMessageBox.critical(self, "Error al exportar", str(e))
            return
        self.status_label.setText("Malla exportada a: {}".format(path))

    # ------------------------------ helpers ----------------------------- #

    def _update_title(self) -> None:
        if self.current_path is None:
            self.setWindowTitle("MeshCAD - sin titulo")
        else:
            self.setWindowTitle("MeshCAD - {}".format(self.current_path))

    def _on_project_replaced(self) -> None:
        # Refrescar paneles que dependen del estado del documento
        self.edges_panel.refresh()

    def _on_generate_mesh(self) -> None:
        meshes, errors = self.document.generate_mesh()
        if errors:
            self.status_label.setText("Errores: " + "; ".join(errors))
        else:
            total_cells = sum(bm.cell_count() for bm in meshes)
            self.status_label.setText(
                "Malla generada: {} bloques, {} celdas".format(
                    len(meshes), total_cells
                )
            )


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
'''

TEST_MAIN_WINDOW = '''from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.gui.document import Document
from meshcad.gui.main_window import MainWindow


def test_main_window_starts_with_empty_document(qtbot):
    w = MainWindow()
    qtbot.addWidget(w)
    assert len(w.document.topology.vertices()) == 0
    assert w.current_path is None
    assert "sin titulo" in w.windowTitle()


def test_main_window_new_clears(qtbot):
    w = MainWindow()
    qtbot.addWidget(w)
    t = w.document.topology
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    t.add_edge(v0, v1, Line(v0.point, v1.point))
    assert len(w.document.topology.edges()) == 1

    w._on_new()
    assert len(w.document.topology.edges()) == 0
    assert w.current_path is None


def test_main_window_save_and_open(qtbot, tmp_path):
    w = MainWindow()
    qtbot.addWidget(w)

    t = w.document.topology
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    t.add_edge(v0, v1, Line(v0.point, v1.point))

    path = tmp_path / "proj.json"
    w._save_to(path)
    assert path.exists()
    assert w.current_path == path

    w._on_new()
    assert len(w.document.topology.edges()) == 0

    w.document.load_from(__import__("meshcad.io.project_io", fromlist=["load_project"]).load_project(path))
    assert len(w.document.topology.edges()) == 1
'''


# =========================================================================== #
# COMMIT 38 - Exportacion VTK
# =========================================================================== #

VTK_IO_PY = '''"""Exportacion de la malla a VTK XML (pvd + vts por bloque).

El formato pvd (ParaView Data) es una coleccion que referencia
ficheros .vts (VTK XML StructuredGrid), uno por bloque. ParaView
abre el .pvd y muestra todos los bloques a la vez.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from meshcad.core.mesh.generator import BlockMesh


def export_mesh_vtk(block_meshes: List[BlockMesh], pvd_path) -> None:
    """Escribe un .pvd y una carpeta de .vts con las mallas de los bloques."""
    pvd_path = Path(pvd_path)
    pvd_path.parent.mkdir(parents=True, exist_ok=True)

    block_dir = pvd_path.parent / (pvd_path.stem + "_blocks")
    block_dir.mkdir(parents=True, exist_ok=True)

    entries: List[str] = []
    for bm in block_meshes:
        fname = "block_{:04d}.vts".format(bm.block_id)
        _write_structured_grid(block_dir / fname, bm)
        entries.append(fname)

    _write_pvd(pvd_path, entries, block_dir)


def _write_structured_grid(path: Path, bm: BlockMesh) -> None:
    grid = bm.grid
    n_v = len(grid)
    n_u = len(grid[0]) if n_v else 0

    ext = "0 {} 0 {} 0 0".format(max(n_u - 1, 0), max(n_v - 1, 0))

    coords_parts: List[str] = []
    for j in range(n_v):
        for i in range(n_u):
            p = grid[j][i]
            coords_parts.append(
                "{:.17g} {:.17g} 0".format(float(p.x), float(p.y))
            )
    coords = " ".join(coords_parts)

    xml = (
        '<?xml version="1.0"?>\\n'
        '<VTKFile type="StructuredGrid" version="0.1" '
        'byte_order="LittleEndian">\\n'
        '  <StructuredGrid WholeExtent="{ext}">\\n'
        '    <Piece Extent="{ext}">\\n'
        '      <Points>\\n'
        '        <DataArray type="Float64" NumberOfComponents="3" '
        'format="ascii">\\n'
        '          {coords}\\n'
        '        </DataArray>\\n'
        '      </Points>\\n'
        '    </Piece>\\n'
        '  </StructuredGrid>\\n'
        '</VTKFile>\\n'
    ).format(ext=ext, coords=coords)

    path.write_text(xml, encoding="utf-8")


def _write_pvd(pvd_path: Path, entries: List[str], block_dir: Path) -> None:
    rel = os.path.relpath(block_dir, pvd_path.parent).replace("\\\\", "/")
    rel = rel.replace("\\\\", "/")
    if rel == ".":
        rel = ""

    lines = [
        '<?xml version="1.0"?>',
        '<VTKFile type="Collection" version="0.1">',
        "  <Collection>",
    ]
    for i, entry in enumerate(entries):
        relpath = "{}/{}".format(rel, entry) if rel else entry
        lines.append(
            '    <DataSet timestep="0" group="" part="{}" file="{}"/>'.format(
                i, relpath
            )
        )
    lines += ["  </Collection>", "</VTKFile>", ""]
    pvd_path.write_text("\\n".join(lines), encoding="utf-8")
'''

IO_INIT_FINAL = '''"""Persistencia (JSON) y exportacion (VTK)."""

from meshcad.io.json_io import (
    block_from_dict,
    block_side_from_dict,
    block_side_to_dict,
    block_to_dict,
    distribution_from_dict,
    distribution_to_dict,
    edge_spec_from_dict,
    edge_spec_to_dict,
    geometry_from_dict,
    geometry_to_dict,
    topology_from_dict,
    topology_to_dict,
)
from meshcad.io.project_io import load_project, save_project
from meshcad.io.vtk_io import export_mesh_vtk

__all__ = [
    "geometry_to_dict",
    "geometry_from_dict",
    "distribution_to_dict",
    "distribution_from_dict",
    "topology_to_dict",
    "topology_from_dict",
    "edge_spec_to_dict",
    "edge_spec_from_dict",
    "block_side_to_dict",
    "block_side_from_dict",
    "block_to_dict",
    "block_from_dict",
    "save_project",
    "load_project",
    "export_mesh_vtk",
]
'''

TEST_VTK = '''from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.mesh.distribution import UniformDistribution
from meshcad.core.mesh.model import EdgeMeshSpec
from meshcad.core.topology.block import Block
from meshcad.core.topology.loop import Loop
from meshcad.gui.document import Document
from meshcad.io.vtk_io import export_mesh_vtk


def build_meshed_document(n_nodes=4):
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
    for e in (e0, e1, e2, e3):
        doc.set_edge_spec(EdgeMeshSpec(e.id, n_nodes, UniformDistribution()))
    doc.generate_mesh()
    return doc


def test_export_creates_pvd_and_blocks_dir(tmp_path):
    doc = build_meshed_document()
    pvd = tmp_path / "malla.pvd"
    export_mesh_vtk(doc.block_meshes, pvd)
    assert pvd.exists()
    blocks_dir = tmp_path / "malla_blocks"
    assert blocks_dir.is_dir()
    assert (blocks_dir / "block_0000.vts").exists()


def test_pvd_contains_reference(tmp_path):
    doc = build_meshed_document()
    pvd = tmp_path / "malla.pvd"
    export_mesh_vtk(doc.block_meshes, pvd)
    content = pvd.read_text(encoding="utf-8")
    assert "block_0000.vts" in content
    assert "Collection" in content


def test_vts_contains_structured_grid(tmp_path):
    doc = build_meshed_document(n_nodes=4)
    pvd = tmp_path / "malla.pvd"
    export_mesh_vtk(doc.block_meshes, pvd)
    vts = (tmp_path / "malla_blocks" / "block_0000.vts").read_text(encoding="utf-8")
    assert "StructuredGrid" in vts
    assert 'WholeExtent="0 3 0 3 0 0"' in vts
    assert "Float64" in vts


def test_export_multiple_blocks(tmp_path):
    doc = build_meshed_document()
    pvd = tmp_path / "malla.pvd"
    export_mesh_vtk(doc.block_meshes, pvd)
    blocks_dir = tmp_path / "malla_blocks"
    vts_files = sorted(blocks_dir.glob("*.vts"))
    assert len(vts_files) == len(doc.block_meshes)
'''

IO_INIT = IO_INIT_FINAL


# =========================================================================== #
# Ejecucion
# =========================================================================== #

def main():
    check()

    commit(
        "Commit 34/38: JSON geometria y distribuciones",
        {
            "src/meshcad/io/__init__.py": IO_INIT_STEP34,
            "src/meshcad/io/json_io.py": JSON_IO_PY,
            "tests/io/__init__.py": "",
            "tests/io/test_json_geometry.py": TEST_JSON_GEOM,
        },
        "feat(io): serializacion JSON de geometria y distribuciones",
    )

    # Patch Topology with _load_state before commit 35 tests
    topology_path = ROOT / "src" / "meshcad" / "core" / "topology" / "topology.py"
    topo_content = topology_path.read_text(encoding="utf-8")
    marker = "    # ------------------------------- misc ------------------------------- #"
    if marker not in topo_content:
        print("ERROR: no encuentro el marcador en topology.py")
        sys.exit(1)
    topo_content = topo_content.replace(marker, TOPOLOGY_LOAD_PATCH + "\n" + marker)
    topology_path.write_text(topo_content, encoding="utf-8")
    print("  ~ src/meshcad/core/topology/topology.py (anadido _load_state)")

    commit(
        "Commit 35/38: JSON topologia y bloques",
        {
            "src/meshcad/io/__init__.py": IO_INIT_STEP35,
            "src/meshcad/io/json_io.py": JSON_IO_FULL,
            "tests/io/test_json_topology.py": TEST_JSON_TOPOLOGY,
        },
        "feat(io): serializacion JSON de topologia, malla y bloques",
    )

    commit(
        "Commit 36/38: Document.save / load",
        {
            "src/meshcad/io/project_io.py": PROJECT_IO_PY,
            "src/meshcad/gui/document.py": DOCUMENT_PY,
            "src/meshcad/io/__init__.py": JSON_IO_SAVE,
            "tests/io/test_project_io.py": TEST_PROJECT_IO,
        },
        "feat(io): save/load de proyecto completo y Document.load_from",
    )

    commit(
        "Commit 37/38: Menu Archivo",
        {
            "src/meshcad/gui/main_window.py": MAIN_WINDOW_PY,
            "tests/gui/test_main_window.py": TEST_MAIN_WINDOW,
        },
        "feat(gui): menu Archivo con nuevo, abrir, guardar y guardar como",
    )

    commit(
        "Commit 38/38: Exportacion VTK",
        {
            "src/meshcad/io/vtk_io.py": VTK_IO_PY,
            "src/meshcad/io/__init__.py": IO_INIT,
            "tests/io/test_vtk.py": TEST_VTK,
        },
        "feat(io): exportacion de malla a VTK XML (pvd + vts)",
    )

    print()
    print("== Verificando todos los tests ==")
    run([sys.executable, "-m", "pytest", "-q"])

    print()
    print("== Historial ==")
    run(["git", "log", "--oneline", "--decorate"])

    print()
    print("Fase 7 completada. Ejecuta 'python -m meshcad'.")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print()
        print("ERROR:", e)
        sys.exit(1)