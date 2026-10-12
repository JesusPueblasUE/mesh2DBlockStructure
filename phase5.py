#!/usr/bin/env python3
"""
Fase 5 del proyecto MeshCAD: distribuciones de nodos.

Crea los commits atomicos de la fase 5:
evaluate(t), NodeDistribution, BiasedDistribution,
EdgeMeshSpec, MeshModel y paneles GUI.

Uso:
    cd meshcad
    python phase5.py
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
# COMMIT 24 - evaluate(t) en las geometrias
# =========================================================================== #

ENTITY_PY = '''"""Clase base abstracta para las entidades geometricas 2D."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Tuple

from meshcad.core.geometry.point import Point2D


class GeometryEntity(ABC):
    """Interfaz comun a todas las entidades geometricas 2D."""

    @abstractmethod
    def start_point(self) -> Point2D:
        """Punto inicial de la entidad."""

    @abstractmethod
    def end_point(self) -> Point2D:
        """Punto final de la entidad."""

    @abstractmethod
    def length(self) -> float:
        """Longitud total de la entidad."""

    @abstractmethod
    def evaluate(self, t: float) -> Point2D:
        """Evalua la entidad en el parametro normalizado t en [0, 1].

        t=0 devuelve start_point, t=1 devuelve end_point.
        """

    @abstractmethod
    def sample(self, n: int) -> List[Point2D]:
        """Devuelve n puntos equiespaciados en t, incluyendo los extremos."""

    @abstractmethod
    def bounding_box(self) -> Tuple[Point2D, Point2D]:
        """Devuelve (min_point, max_point) del rectangulo que la contiene."""
'''

LINE_PY = '''"""Segmento de recta."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from meshcad.core.geometry.entity import GeometryEntity
from meshcad.core.geometry.point import Point2D


@dataclass(frozen=True)
class Line(GeometryEntity):
    """Segmento de recta definido por dos puntos."""

    start: Point2D
    end: Point2D

    def start_point(self) -> Point2D:
        return self.start

    def end_point(self) -> Point2D:
        return self.end

    def length(self) -> float:
        return self.start.distance_to(self.end)

    def evaluate(self, t: float) -> Point2D:
        t = max(0.0, min(1.0, t))
        return Point2D(
            self.start.x + (self.end.x - self.start.x) * t,
            self.start.y + (self.end.y - self.start.y) * t,
        )

    def sample(self, n: int) -> List[Point2D]:
        if n < 2:
            raise ValueError("n debe ser >= 2")
        return [self.evaluate(i / (n - 1)) for i in range(n)]

    def bounding_box(self) -> Tuple[Point2D, Point2D]:
        return (
            Point2D(min(self.start.x, self.end.x), min(self.start.y, self.end.y)),
            Point2D(max(self.start.x, self.end.x), max(self.start.y, self.end.y)),
        )
'''

ARC_PY = '''"""Arco de circulo recorrido en sentido antihorario."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple

from meshcad.core.geometry.entity import GeometryEntity
from meshcad.core.geometry.point import Point2D

TWO_PI = 2.0 * math.pi


@dataclass(frozen=True)
class Arc(GeometryEntity):
    """Arco de circulo definido por centro, radio y angulos (radianes).

    El arco se recorre en sentido antihorario desde start_angle hasta
    end_angle. Si end_angle < start_angle, el barrido se completa sumando
    2*pi.
    """

    center: Point2D
    radius: float
    start_angle: float
    end_angle: float

    def __post_init__(self):
        if self.radius <= 0:
            raise ValueError("El radio debe ser positivo")

    def angle_span(self) -> float:
        span = self.end_angle - self.start_angle
        while span <= 0:
            span += TWO_PI
        return span

    def point_at_angle(self, angle: float) -> Point2D:
        return Point2D(
            self.center.x + self.radius * math.cos(angle),
            self.center.y + self.radius * math.sin(angle),
        )

    def start_point(self) -> Point2D:
        return self.point_at_angle(self.start_angle)

    def end_point(self) -> Point2D:
        return self.point_at_angle(self.end_angle)

    def length(self) -> float:
        return self.radius * self.angle_span()

    def evaluate(self, t: float) -> Point2D:
        t = max(0.0, min(1.0, t))
        return self.point_at_angle(self.start_angle + self.angle_span() * t)

    def sample(self, n: int) -> List[Point2D]:
        if n < 2:
            raise ValueError("n debe ser >= 2")
        return [self.evaluate(i / (n - 1)) for i in range(n)]

    def bounding_box(self) -> Tuple[Point2D, Point2D]:
        pts = [self.start_point(), self.end_point()]
        for k in range(4):
            a = k * math.pi / 2
            if self._angle_in_span(a):
                pts.append(self.point_at_angle(a))
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        return (Point2D(min(xs), min(ys)), Point2D(max(xs), max(ys)))

    def _angle_in_span(self, angle: float) -> bool:
        delta = (angle - self.start_angle) % TWO_PI
        return delta <= self.angle_span() + 1e-9
'''

SPLINE_PY = '''"""Spline interpolante (Catmull-Rom) por una lista de puntos."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple

from meshcad.core.geometry.entity import GeometryEntity
from meshcad.core.geometry.point import Point2D


def _catmull_rom(p0: Point2D, p1: Point2D, p2: Point2D, p3: Point2D,
                 t: float) -> Point2D:
    t2 = t * t
    t3 = t2 * t
    x = 0.5 * (
        2.0 * p1.x
        + (-p0.x + p2.x) * t
        + (2.0 * p0.x - 5.0 * p1.x + 4.0 * p2.x - p3.x) * t2
        + (-p0.x + 3.0 * p1.x - 3.0 * p2.x + p3.x) * t3
    )
    y = 0.5 * (
        2.0 * p1.y
        + (-p0.y + p2.y) * t
        + (2.0 * p0.y - 5.0 * p1.y + 4.0 * p2.y - p3.y) * t2
        + (-p0.y + 3.0 * p1.y - 3.0 * p2.y + p3.y) * t3
    )
    return Point2D(x, y)


@dataclass(frozen=True)
class Spline(GeometryEntity):
    """Spline interpolante Catmull-Rom que pasa por todos los puntos."""

    points: Tuple[Point2D, ...]

    def __post_init__(self):
        if len(self.points) < 2:
            raise ValueError("Una spline necesita al menos 2 puntos")

    def start_point(self) -> Point2D:
        return self.points[0]

    def end_point(self) -> Point2D:
        return self.points[-1]

    def evaluate(self, t: float) -> Point2D:
        n = len(self.points)
        if n == 2:
            a, b = self.points
            t = max(0.0, min(1.0, t))
            return Point2D(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t)

        t = max(0.0, min(1.0, t))
        segments = n - 1
        scaled = t * segments
        i = min(int(scaled), segments - 1)
        local_t = scaled - i

        p0 = self.points[i - 1] if i - 1 >= 0 else self.points[0]
        p1 = self.points[i]
        p2 = self.points[i + 1]
        p3 = self.points[i + 2] if i + 2 < n else self.points[-1]

        return _catmull_rom(p0, p1, p2, p3, local_t)

    def sample(self, n: int) -> List[Point2D]:
        if n < 2:
            raise ValueError("n debe ser >= 2")
        return [self.evaluate(i / (n - 1)) for i in range(n)]

    def length(self) -> float:
        dense = self.sample(200)
        return sum(
            dense[i].distance_to(dense[i + 1]) for i in range(len(dense) - 1)
        )

    def bounding_box(self) -> Tuple[Point2D, Point2D]:
        pts = self.sample(200)
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        return (Point2D(min(xs), min(ys)), Point2D(max(xs), max(ys)))
'''

TEST_ENTITY = '''import pytest

from meshcad.core.geometry.entity import GeometryEntity
from meshcad.core.geometry.point import Point2D


def test_cannot_instantiate_abstract():
    with pytest.raises(TypeError):
        GeometryEntity()  # type: ignore[abstract]


def test_subclass_must_implement_all_methods():
    class Incomplete(GeometryEntity):
        def start_point(self):
            return Point2D(0, 0)

    with pytest.raises(TypeError):
        Incomplete()  # type: ignore[abstract]


def test_complete_subclass_can_be_instantiated():
    class Dummy(GeometryEntity):
        def start_point(self):
            return Point2D(0, 0)

        def end_point(self):
            return Point2D(1, 0)

        def length(self):
            return 1.0

        def evaluate(self, t):
            return Point2D(t, 0.0)

        def sample(self, n):
            return [Point2D(0, 0), Point2D(1, 0)]

        def bounding_box(self):
            return (Point2D(0, 0), Point2D(1, 0))

    d = Dummy()
    assert d.length() == 1.0
    assert d.start_point() == Point2D(0, 0)
'''

TEST_EVALUATE = '''import math

from meshcad.core.geometry.arc import Arc
from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.geometry.spline import Spline


def test_line_evaluate_endpoints():
    line = Line(Point2D(0, 0), Point2D(10, 0))
    assert line.evaluate(0.0) == Point2D(0, 0)
    assert line.evaluate(1.0) == Point2D(10, 0)


def test_line_evaluate_midpoint():
    line = Line(Point2D(0, 0), Point2D(10, 0))
    mid = line.evaluate(0.5)
    assert math.isclose(mid.x, 5.0)
    assert math.isclose(mid.y, 0.0)


def test_line_sample_uses_evaluate():
    line = Line(Point2D(0, 0), Point2D(4, 0))
    assert line.sample(5) == [
        Point2D(0, 0), Point2D(1, 0), Point2D(2, 0), Point2D(3, 0), Point2D(4, 0)
    ]


def test_arc_evaluate_endpoints():
    arc = Arc(Point2D(0, 0), 1.0, 0.0, math.pi / 2)
    s = arc.evaluate(0.0)
    e = arc.evaluate(1.0)
    assert math.isclose(s.x, 1.0)
    assert math.isclose(s.y, 0.0, abs_tol=1e-12)
    assert math.isclose(e.x, 0.0, abs_tol=1e-12)
    assert math.isclose(e.y, 1.0)


def test_arc_evaluate_midpoint_quarter():
    arc = Arc(Point2D(0, 0), 1.0, 0.0, math.pi / 2)
    mid = arc.evaluate(0.5)
    assert math.isclose(mid.x, math.cos(math.pi / 4))
    assert math.isclose(mid.y, math.sin(math.pi / 4))


def test_spline_evaluate_endpoints():
    s = Spline((Point2D(0, 0), Point2D(1, 2), Point2D(3, 1)))
    assert s.evaluate(0.0) == Point2D(0, 0)
    assert s.evaluate(1.0) == Point2D(3, 1)


def test_spline_sample_uses_evaluate():
    s = Spline((Point2D(0, 0), Point2D(1, 1)))
    pts = s.sample(3)
    assert len(pts) == 3
    assert pts[0] == Point2D(0, 0)
    assert pts[-1] == Point2D(1, 1)
    assert math.isclose(pts[1].x, 0.5)
'''


# =========================================================================== #
# COMMIT 25 - NodeDistribution + UniformDistribution
# =========================================================================== #

DISTRIBUTION_PY = '''"""Distribuciones de nodos a lo largo de una entidad geometrica."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from meshcad.core.geometry.entity import GeometryEntity
from meshcad.core.geometry.point import Point2D


class NodeDistribution(ABC):
    """Interfaz de las distribuciones de nodos.

    Una distribucion produce una lista de parametros t en [0, 1],
    estrictamente creciente, con el primero igual a 0 y el ultimo a 1.
    La conversion a puntos la hace la entidad geometrica via evaluate().
    """

    @abstractmethod
    def positions(self, n: int) -> List[float]:
        """Devuelve n parametros en [0, 1] con extremos fijos."""

    def sample(self, geometry: GeometryEntity, n: int) -> List[Point2D]:
        return [geometry.evaluate(t) for t in self.positions(n)]

    def __repr__(self) -> str:  # pragma: no cover
        return self.__class__.__name__ + "()"


class UniformDistribution(NodeDistribution):
    """Distribucion equiespaciada en el parametro t."""

    def positions(self, n: int) -> List[float]:
        if n < 2:
            raise ValueError("n debe ser >= 2")
        return [i / (n - 1) for i in range(n)]
'''

MESH_INIT = '''"""Generacion de malla estructurada y distribuciones de nodos."""

from meshcad.core.mesh.distribution import NodeDistribution, UniformDistribution

__all__ = ["NodeDistribution", "UniformDistribution"]
'''

TEST_DISTRIBUTION = '''import math

import pytest

from meshcad.core.geometry.arc import Arc
from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.mesh.distribution import (
    NodeDistribution,
    UniformDistribution,
)


def test_abstract_cannot_instantiate():
    with pytest.raises(TypeError):
        NodeDistribution()  # type: ignore[abstract]


def test_uniform_positions_endpoints():
    d = UniformDistribution()
    ts = d.positions(5)
    assert math.isclose(ts[0], 0.0)
    assert math.isclose(ts[-1], 1.0)
    assert len(ts) == 5


def test_uniform_positions_equally_spaced():
    d = UniformDistribution()
    ts = d.positions(4)
    assert math.isclose(ts[1], 1.0 / 3.0)
    assert math.isclose(ts[2], 2.0 / 3.0)


def test_uniform_requires_min_two():
    d = UniformDistribution()
    with pytest.raises(ValueError):
        d.positions(1)


def test_uniform_samples_on_line():
    d = UniformDistribution()
    line = Line(Point2D(0, 0), Point2D(10, 0))
    pts = d.sample(line, 3)
    assert pts == [Point2D(0, 0), Point2D(5, 0), Point2D(10, 0)]


def test_uniform_samples_on_arc():
    d = UniformDistribution()
    arc = Arc(Point2D(0, 0), 1.0, 0.0, math.pi / 2)
    pts = d.sample(arc, 3)
    assert math.isclose(pts[1].x, math.cos(math.pi / 4))
    assert math.isclose(pts[1].y, math.sin(math.pi / 4))
'''


# =========================================================================== #
# COMMIT 26 - BiasedDistribution
# =========================================================================== #

DISTRIBUTION_BIASED_PY = '''"""Distribuciones de nodos a lo largo de una entidad geometrica."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from meshcad.core.geometry.entity import GeometryEntity
from meshcad.core.geometry.point import Point2D


class NodeDistribution(ABC):
    """Interfaz de las distribuciones de nodos.

    Una distribucion produce una lista de parametros t en [0, 1],
    estrictamente creciente, con el primero igual a 0 y el ultimo a 1.
    """

    @abstractmethod
    def positions(self, n: int) -> List[float]:
        """Devuelve n parametros en [0, 1] con extremos fijos."""

    def sample(self, geometry: GeometryEntity, n: int) -> List[Point2D]:
        return [geometry.evaluate(t) for t in self.positions(n)]

    def __repr__(self) -> str:  # pragma: no cover
        return self.__class__.__name__ + "()"


class UniformDistribution(NodeDistribution):
    """Distribucion equiespaciada en el parametro t."""

    def positions(self, n: int) -> List[float]:
        if n < 2:
            raise ValueError("n debe ser >= 2")
        return [i / (n - 1) for i in range(n)]


@dataclass(frozen=True)
class BiasedDistribution(NodeDistribution):
    """Distribucion con espaciado geometrico.

    Los intervalos entre nodos crecen en progresion geometrica de razon
    'bias'. bias=1.0 equivale a uniforme. bias>1 concentra nodos al
    principio (from_start=True) o al final (from_start=False).
    """

    bias: float = 2.0
    from_start: bool = True

    def __post_init__(self):
        if self.bias <= 0:
            raise ValueError("bias debe ser > 0")

    def positions(self, n: int) -> List[float]:
        if n < 2:
            raise ValueError("n debe ser >= 2")

        if abs(self.bias - 1.0) < 1e-12:
            return [i / (n - 1) for i in range(n)]

        r = self.bias
        denom = r ** (n - 1) - 1.0
        ts = [(r ** i - 1.0) / denom for i in range(n)]

        if self.from_start:
            return ts
        return [1.0 - t for t in reversed(ts)]

    def __repr__(self) -> str:
        return "BiasedDistribution(bias={:g}, from_start={})".format(
            self.bias, self.from_start
        )
'''

MESH_INIT_BIASED = '''"""Generacion de malla estructurada y distribuciones de nodos."""

from meshcad.core.mesh.distribution import (
    BiasedDistribution,
    NodeDistribution,
    UniformDistribution,
)

__all__ = [
    "NodeDistribution",
    "UniformDistribution",
    "BiasedDistribution",
]
'''

TEST_BIASED = '''import math

import pytest

from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.mesh.distribution import BiasedDistribution


def test_rejects_nonpositive_bias():
    with pytest.raises(ValueError):
        BiasedDistribution(bias=0.0)
    with pytest.raises(ValueError):
        BiasedDistribution(bias=-1.0)


def test_bias_one_equals_uniform():
    d = BiasedDistribution(bias=1.0)
    ts = d.positions(5)
    expected = [i / 4 for i in range(5)]
    for a, b in zip(ts, expected):
        assert math.isclose(a, b)


def test_endpoints_fixed():
    d = BiasedDistribution(bias=2.0)
    ts = d.positions(6)
    assert math.isclose(ts[0], 0.0)
    assert math.isclose(ts[-1], 1.0)


def test_strictly_increasing():
    d = BiasedDistribution(bias=1.5)
    ts = d.positions(8)
    for i in range(len(ts) - 1):
        assert ts[i] < ts[i + 1]


def test_bias_gt_one_clusters_at_start():
    # Con bias > 1 los primeros intervalos son menores
    d = BiasedDistribution(bias=2.0, from_start=True)
    ts = d.positions(6)
    first_interval = ts[1] - ts[0]
    last_interval = ts[-1] - ts[-2]
    assert first_interval < last_interval


def test_bias_gt_one_from_end_clusters_at_end():
    d = BiasedDistribution(bias=2.0, from_start=False)
    ts = d.positions(6)
    first_interval = ts[1] - ts[0]
    last_interval = ts[-1] - ts[-2]
    assert first_interval > last_interval


def test_sample_on_line():
    d = BiasedDistribution(bias=2.0)
    line = Line(Point2D(0, 0), Point2D(1, 0))
    pts = d.sample(line, 5)
    assert len(pts) == 5
    assert math.isclose(pts[0].x, 0.0)
    assert math.isclose(pts[-1].x, 1.0)
'''


# =========================================================================== #
# COMMIT 27 - EdgeMeshSpec + MeshModel
# =========================================================================== #

MESH_MODEL_PY = '''"""Modelo de malla: distribuciones por arista y consultas por lado."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from meshcad.core.geometry.point import Point2D
from meshcad.core.mesh.distribution import (
    NodeDistribution,
    UniformDistribution,
)
from meshcad.core.topology.block_side import BlockSide
from meshcad.core.topology.topology import Topology

DEFAULT_N_NODES = 5


@dataclass
class EdgeMeshSpec:
    """Especificacion de malla de una arista.

    n_nodes es el numero total de nodos, incluyendo ambos extremos.
    distribution define como se reparten en el parametro t en [0, 1].
    """

    edge_id: int
    n_nodes: int
    distribution: NodeDistribution

    def __post_init__(self):
        if self.n_nodes < 2:
            raise ValueError("n_nodes debe ser >= 2")


class MeshModel:
    """Distribuciones de nodos asociadas a las aristas.

    Una misma arista puede pertenecer a varios bloques; la distribucion
    se guarda una sola vez y todos los bloques la comparten.
    """

    def __init__(self) -> None:
        self.edge_specs: Dict[int, EdgeMeshSpec] = {}

    # ----------------------------- acceso ------------------------------- #

    def get_spec(self, edge_id: int) -> EdgeMeshSpec:
        spec = self.edge_specs.get(edge_id)
        if spec is None:
            return EdgeMeshSpec(edge_id, DEFAULT_N_NODES, UniformDistribution())
        return spec

    def set_spec(self, spec: EdgeMeshSpec) -> None:
        self.edge_specs[spec.edge_id] = spec

    def clear_spec(self, edge_id: int) -> None:
        self.edge_specs.pop(edge_id, None)

    # ----------------------------- consultas ---------------------------- #

    def side_node_count(self, side: BlockSide) -> int:
        """Numero de nodos de un lado concatenando sus aristas.

        Si el lado tiene k aristas con n_0, ..., n_{k-1} nodos cada una,
        el total es sum(n_i) - (k - 1), porque los extremos de aristas
        consecutivas se solapan en un vertice.
        """
        if not side.oriented_edges:
            return 0
        total = 0
        for i, oe in enumerate(side.oriented_edges):
            spec = self.get_spec(oe.edge_id)
            total += spec.n_nodes if i == 0 else spec.n_nodes - 1
        return total

    def side_samples(self, side: BlockSide, topology: Topology) -> List[Point2D]:
        """Puntos a lo largo de un lado, en el orden de recorrido."""
        samples: List[Point2D] = []
        for i, oe in enumerate(side.oriented_edges):
            edge = topology.get_edge(oe.edge_id)
            spec = self.get_spec(oe.edge_id)
            pts = spec.distribution.sample(edge.geometry, spec.n_nodes)
            if oe.reversed:
                pts = list(reversed(pts))
            if i > 0:
                pts = pts[1:]
            samples.extend(pts)
        return samples
'''

MESH_INIT_MODEL = '''"""Generacion de malla estructurada y distribuciones de nodos."""

from meshcad.core.mesh.distribution import (
    BiasedDistribution,
    NodeDistribution,
    UniformDistribution,
)
from meshcad.core.mesh.model import EdgeMeshSpec, MeshModel, DEFAULT_N_NODES

__all__ = [
    "NodeDistribution",
    "UniformDistribution",
    "BiasedDistribution",
    "EdgeMeshSpec",
    "MeshModel",
    "DEFAULT_N_NODES",
]
'''

TEST_MESH_MODEL = '''import math

import pytest

from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.mesh.distribution import (
    BiasedDistribution,
    UniformDistribution,
)
from meshcad.core.mesh.model import DEFAULT_N_NODES, EdgeMeshSpec, MeshModel
from meshcad.core.topology.block_side import BlockSide
from meshcad.core.topology.edge import OrientedEdge
from meshcad.core.topology.topology import Topology


def test_edge_spec_requires_two_nodes():
    with pytest.raises(ValueError):
        EdgeMeshSpec(0, 1, UniformDistribution())


def test_default_spec_is_uniform():
    m = MeshModel()
    spec = m.get_spec(42)
    assert spec.n_nodes == DEFAULT_N_NODES
    assert isinstance(spec.distribution, UniformDistribution)


def test_set_and_get_spec():
    m = MeshModel()
    spec = EdgeMeshSpec(3, 7, BiasedDistribution(bias=1.5))
    m.set_spec(spec)
    assert m.get_spec(3) is spec


def test_clear_spec_returns_default():
    m = MeshModel()
    m.set_spec(EdgeMeshSpec(0, 9, UniformDistribution()))
    m.clear_spec(0)
    assert m.get_spec(0).n_nodes == DEFAULT_N_NODES


def test_side_node_count_single_edge():
    m = MeshModel()
    m.set_spec(EdgeMeshSpec(0, 6, UniformDistribution()))
    side = BlockSide((OrientedEdge(0),))
    assert m.side_node_count(side) == 6


def test_side_node_count_two_edges_overlap():
    m = MeshModel()
    m.set_spec(EdgeMeshSpec(0, 5, UniformDistribution()))
    m.set_spec(EdgeMeshSpec(1, 4, UniformDistribution()))
    side = BlockSide((OrientedEdge(0), OrientedEdge(1)))
    # 5 + 4 - 1 = 8
    assert m.side_node_count(side) == 8


def test_side_node_count_defaults_used_when_unset():
    m = MeshModel()
    side = BlockSide((OrientedEdge(0),))
    assert m.side_node_count(side) == DEFAULT_N_NODES


def test_side_samples_single_edge():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(10, 0))
    e = t.add_edge(v0, v1, Line(v0.point, v1.point))

    m = MeshModel()
    m.set_spec(EdgeMeshSpec(e.id, 3, UniformDistribution()))

    side = BlockSide((OrientedEdge(e.id),))
    pts = m.side_samples(side, t)
    assert pts == [Point2D(0, 0), Point2D(5, 0), Point2D(10, 0)]


def test_side_samples_reversed_edge():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(10, 0))
    e = t.add_edge(v0, v1, Line(v0.point, v1.point))

    m = MeshModel()
    m.set_spec(EdgeMeshSpec(e.id, 3, UniformDistribution()))

    side = BlockSide((OrientedEdge(e.id, reversed=True),))
    pts = m.side_samples(side, t)
    assert pts == [Point2D(10, 0), Point2D(5, 0), Point2D(0, 0)]


def test_side_samples_two_edges_no_duplicate_joint():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(10, 0))
    v2 = t.add_vertex(Point2D(10, 10))
    e0 = t.add_edge(v0, v1, Line(v0.point, v1.point))
    e1 = t.add_edge(v1, v2, Line(v1.point, v2.point))

    m = MeshModel()
    m.set_spec(EdgeMeshSpec(e0.id, 3, UniformDistribution()))
    m.set_spec(EdgeMeshSpec(e1.id, 3, UniformDistribution()))

    side = BlockSide((OrientedEdge(e0.id), OrientedEdge(e1.id)))
    pts = m.side_samples(side, t)
    assert len(pts) == 5  # 3 + 3 - 1
    assert pts[0] == Point2D(0, 0)
    assert pts[2] == Point2D(10, 0)
    assert pts[-1] == Point2D(10, 10)
'''


# =========================================================================== #
# COMMIT 28 - GUI: Document con MeshModel + panel de aristas
# =========================================================================== #

DOCUMENT_PY = '''"""Documento: estado del proyecto (topologia, malla y bloques)."""

from __future__ import annotations

from typing import List

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QUndoStack

from meshcad.core.mesh.model import EdgeMeshSpec, MeshModel
from meshcad.core.topology.block import Block
from meshcad.core.topology.topology import Topology


class Document(QObject):
    """Estado del proyecto."""

    topology_changed = pyqtSignal()
    mesh_changed = pyqtSignal()
    blocks_changed = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.topology = Topology()
        self.mesh = MeshModel()
        self.blocks: List[Block] = []
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
        """Actualiza el node_count de cada lado desde el modelo de malla."""
        for block in self.blocks:
            for side in block.sides:
                side.node_count = self.mesh.side_node_count(side)
        self.blocks_changed.emit()

    # ------------------------------- mesh ------------------------------- #

    def set_edge_spec(self, spec: EdgeMeshSpec) -> None:
        self.mesh.set_spec(spec)
        self.mesh_changed.emit()
        self.recompute_blocks()
'''

EDGES_PANEL_PY = '''"""Panel para editar la especificacion de malla de cada arista."""

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
'''

MAIN_WINDOW_PY = '''"""Ventana principal de MeshCAD."""

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAction, QApplication, QMainWindow, QToolBar

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

        self.document.topology_changed.connect(self.edges_panel.refresh)

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

TEST_DOCUMENT = '''from meshcad.core.mesh.distribution import UniformDistribution
from meshcad.core.mesh.model import EdgeMeshSpec
from meshcad.core.topology.block import Block
from meshcad.core.topology.block_side import BlockSide
from meshcad.core.topology.edge import OrientedEdge
from meshcad.gui.document import Document


def test_document_starts_empty():
    doc = Document()
    assert len(doc.topology.vertices()) == 0
    assert len(doc.blocks) == 0
    assert len(doc.mesh.edge_specs) == 0


def test_set_edge_spec_emits_mesh_changed(qtbot):
    doc = Document()
    with qtbot.waitSignal(doc.mesh_changed, timeout=1000):
        doc.set_edge_spec(EdgeMeshSpec(0, 7, UniformDistribution()))
    assert doc.mesh.get_spec(0).n_nodes == 7


def test_recompute_blocks_updates_node_counts(qtbot):
    doc = Document()
    sides = tuple(BlockSide((OrientedEdge(i),)) for i in range(4))
    block = Block(0, sides)
    doc.blocks.append(block)

    doc.set_edge_spec(EdgeMeshSpec(0, 5, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(1, 7, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(2, 5, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(3, 7, UniformDistribution()))

    assert block.sides[0].node_count == 5
    assert block.sides[1].node_count == 7
    assert block.sides[2].node_count == 5
    assert block.sides[3].node_count == 7
    block.validate_opposite_sides()


def test_opposite_sides_mismatch_raises_after_recompute(qtbot):
    import pytest

    doc = Document()
    sides = tuple(BlockSide((OrientedEdge(i),)) for i in range(4))
    block = Block(0, sides)
    doc.blocks.append(block)

    doc.set_edge_spec(EdgeMeshSpec(0, 5, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(1, 6, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(2, 7, UniformDistribution()))  # desajuste
    doc.set_edge_spec(EdgeMeshSpec(3, 6, UniformDistribution()))

    with pytest.raises(ValueError):
        block.validate_opposite_sides()
'''


# =========================================================================== #
# COMMIT 29 - GUI: panel de bloques con validacion
# =========================================================================== #

BLOCKS_PANEL_PY = '''"""Panel con la lista de bloques y el estado de sus lados opuestos."""

from __future__ import annotations

from PyQt5.QtWidgets import (
    QDockWidget,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from meshcad.gui.document import Document


class BlocksPanel(QDockWidget):
    """Muestra los bloques y si sus lados opuestos son coherentes."""

    def __init__(self, document: Document, parent=None) -> None:
        super().__init__("Bloques", parent)
        self.document = document

        container = QWidget()
        layout = QVBoxLayout(container)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        self.status = QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.setWidget(container)

        self.document.blocks_changed.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        self.list_widget.clear()
        n_ok = 0
        n_bad = 0
        for block in self.document.blocks:
            n0 = block.sides[0].node_count
            n1 = block.sides[1].node_count
            n2 = block.sides[2].node_count
            n3 = block.sides[3].node_count

            ok_02 = (n0 == n2)
            ok_13 = (n1 == n3)
            if ok_02 and ok_13:
                tag = "OK"
                n_ok += 1
                detail = "(nodos {} x {})".format(n0, n1)
            else:
                tag = "DESAJUSTE"
                n_bad += 1
                msgs = []
                if not ok_02:
                    msgs.append("lados 0/2: {} vs {}".format(n0, n2))
                if not ok_13:
                    msgs.append("lados 1/3: {} vs {}".format(n1, n3))
                detail = "; ".join(msgs)

            item = QListWidgetItem(
                "Bloque {}: {} {}".format(block.id, tag, detail)
            )
            self.list_widget.addItem(item)

        if not self.document.blocks:
            self.status.setText("Sin bloques todavia.")
        else:
            self.status.setText(
                "{} bloques: {} OK, {} con desajustes".format(
                    len(self.document.blocks), n_ok, n_bad
                )
            )
'''

MAIN_WINDOW_PY = '''"""Ventana principal de MeshCAD."""

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAction, QApplication, QMainWindow, QToolBar

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

TEST_BLOCKS_PANEL = '''from meshcad.core.mesh.distribution import UniformDistribution
from meshcad.core.mesh.model import EdgeMeshSpec
from meshcad.core.topology.block import Block
from meshcad.core.topology.block_side import BlockSide
from meshcad.core.topology.edge import OrientedEdge
from meshcad.gui.document import Document


def test_blocks_panel_refresh_without_blocks(qtbot):
    from meshcad.gui.blocks_panel import BlocksPanel

    doc = Document()
    panel = BlocksPanel(doc)
    qtbot.addWidget(panel)
    assert "Sin bloques" in panel.status.text()


def test_blocks_panel_lists_ok_block(qtbot):
    from meshcad.gui.blocks_panel import BlocksPanel

    doc = Document()
    sides = tuple(BlockSide((OrientedEdge(i),)) for i in range(4))
    block = Block(0, sides)
    doc.blocks.append(block)
    doc.set_edge_spec(EdgeMeshSpec(0, 5, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(1, 7, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(2, 5, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(3, 7, UniformDistribution()))

    panel = BlocksPanel(doc)
    qtbot.addWidget(panel)
    assert "1 bloques: 1 OK" in panel.status.text()


def test_blocks_panel_detects_mismatch(qtbot):
    from meshcad.gui.blocks_panel import BlocksPanel

    doc = Document()
    sides = tuple(BlockSide((OrientedEdge(i),)) for i in range(4))
    block = Block(0, sides)
    doc.blocks.append(block)
    doc.set_edge_spec(EdgeMeshSpec(0, 5, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(1, 6, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(2, 8, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(3, 6, UniformDistribution()))

    panel = BlocksPanel(doc)
    qtbot.addWidget(panel)
    assert "0 OK" in panel.status.text()
    assert "1 con desajustes" in panel.status.text()
'''


# =========================================================================== #
# Ejecucion
# =========================================================================== #

def main():
    check()

    commit(
        "Commit 24/29: evaluate(t) en geometrias",
        {
            "src/meshcad/core/geometry/entity.py": ENTITY_PY,
            "src/meshcad/core/geometry/line.py": LINE_PY,
            "src/meshcad/core/geometry/arc.py": ARC_PY,
            "src/meshcad/core/geometry/spline.py": SPLINE_PY,
            "tests/core/geometry/test_entity.py": TEST_ENTITY,
            "tests/core/geometry/test_evaluate.py": TEST_EVALUATE,
        },
        "feat(core): evaluate(t) en Line, Arc y Spline",
    )

    commit(
        "Commit 25/29: NodeDistribution + Uniform",
        {
            "src/meshcad/core/mesh/distribution.py": DISTRIBUTION_PY,
            "src/meshcad/core/mesh/__init__.py": MESH_INIT,
            "tests/core/mesh/__init__.py": "",
            "tests/core/mesh/test_distribution.py": TEST_DISTRIBUTION,
        },
        "feat(core): distribuciones de nodos uniformes",
    )

    commit(
        "Commit 26/29: BiasedDistribution",
        {
            "src/meshcad/core/mesh/distribution.py": DISTRIBUTION_BIASED_PY,
            "src/meshcad/core/mesh/__init__.py": MESH_INIT_BIASED,
            "tests/core/mesh/test_biased.py": TEST_BIASED,
        },
        "feat(core): distribucion con sesgo (biased)",
    )

    commit(
        "Commit 27/29: EdgeMeshSpec + MeshModel",
        {
            "src/meshcad/core/mesh/model.py": MESH_MODEL_PY,
            "src/meshcad/core/mesh/__init__.py": MESH_INIT_MODEL,
            "tests/core/mesh/test_mesh_model.py": TEST_MESH_MODEL,
        },
        "feat(core): especificacion de malla por arista",
    )

    commit(
        "Commit 28/29: Document con MeshModel + panel de aristas",
        {
            "src/meshcad/gui/document.py": DOCUMENT_PY,
            "src/meshcad/gui/edges_panel.py": EDGES_PANEL_PY,
            "src/meshcad/gui/main_window.py": MAIN_WINDOW_PY,
            "tests/gui/test_document.py": TEST_DOCUMENT,
        },
        "feat(gui): panel de edicion de distribuciones por arista",
    )

    commit(
        "Commit 29/29: Panel de bloques con validacion",
        {
            "src/meshcad/gui/blocks_panel.py": BLOCKS_PANEL_PY,
            "src/meshcad/gui/main_window.py": MAIN_WINDOW_PY,
            "tests/gui/test_blocks_panel.py": TEST_BLOCKS_PANEL,
        },
        "feat(gui): panel de bloques con validacion de lados opuestos",
    )

    print()
    print("== Verificando todos los tests ==")
    run([sys.executable, "-m", "pytest", "-q"])

    print()
    print("== Historial ==")
    run(["git", "log", "--oneline", "--decorate"])

    print()
    print("Fase 5 completada. Ejecuta 'python -m meshcad'.")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print()
        print("ERROR:", e)
        sys.exit(1)