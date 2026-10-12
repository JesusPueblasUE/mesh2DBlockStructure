#!/usr/bin/env python3
"""
Fase 1 del proyecto MeshCAD: nucleo geometrico 2D.

Crea los commits atomicos de la fase 1 (Point2D, Vector2D,
GeometryEntity, Line, Arc, Spline).

Uso:
    cd meshcad
    python phase1.py
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


def commit(stage_name, files, msg):
    print()
    print("== " + stage_name + " ==")
    for rel, content in files.items():
        write(rel, content)
    run(["git", "add", "."])
    run(["git", "commit", "-m", msg])


# =========================================================================== #
# COMMIT 1 - Point2D y Vector2D
# =========================================================================== #

POINT_PY = '''"""Punto en el plano 2D."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Point2D:
    """Punto en el plano 2D, inmutable."""

    x: float
    y: float

    def __sub__(self, other: "Point2D") -> "object":
        from meshcad.core.geometry.vector import Vector2D

        return Vector2D(self.x - other.x, self.y - other.y)

    def __add__(self, other) -> "Point2D":
        return Point2D(self.x + other.x, self.y + other.y)

    def distance_to(self, other: "Point2D") -> float:
        return math.hypot(self.x - other.x, self.y - other.y)

    def as_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def __repr__(self) -> str:
        return "Point2D({:g}, {:g})".format(self.x, self.y)
'''

VECTOR_PY = '''"""Vector en el plano 2D."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Vector2D:
    """Vector en el plano 2D, inmutable."""

    x: float
    y: float

    def __add__(self, other: "Vector2D") -> "Vector2D":
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vector2D") -> "Vector2D":
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vector2D":
        return Vector2D(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> "Vector2D":
        return self * scalar

    def __neg__(self) -> "Vector2D":
        return Vector2D(-self.x, -self.y)

    def norm(self) -> float:
        return math.hypot(self.x, self.y)

    def normalized(self) -> "Vector2D":
        n = self.norm()
        if n == 0:
            raise ValueError("No se puede normalizar el vector nulo")
        return Vector2D(self.x / n, self.y / n)

    def dot(self, other: "Vector2D") -> float:
        return self.x * other.x + self.y * other.y

    def cross(self, other: "Vector2D") -> float:
        return self.x * other.y - self.y * other.x

    def angle(self) -> float:
        return math.atan2(self.y, self.x)

    def rotate(self, angle: float) -> "Vector2D":
        c, s = math.cos(angle), math.sin(angle)
        return Vector2D(self.x * c - self.y * s, self.x * s + self.y * c)
'''

GEOMETRY_INIT_STEP1 = '''"""Entidades geometricas 2D: Point2D, Line, Arc, Spline."""

from meshcad.core.geometry.point import Point2D
from meshcad.core.geometry.vector import Vector2D

__all__ = ["Point2D", "Vector2D"]
'''

TEST_POINT = '''import math

from meshcad.core.geometry.point import Point2D
from meshcad.core.geometry.vector import Vector2D


def test_create():
    p = Point2D(1.0, 2.0)
    assert p.x == 1.0
    assert p.y == 2.0


def test_subtraction_gives_vector():
    v = Point2D(3, 4) - Point2D(1, 1)
    assert isinstance(v, Vector2D)
    assert v.x == 2
    assert v.y == 3


def test_addition_with_vector():
    p = Point2D(1, 1) + Vector2D(2, 3)
    assert p == Point2D(3, 4)


def test_distance():
    d = Point2D(0, 0).distance_to(Point2D(3, 4))
    assert math.isclose(d, 5.0)


def test_as_tuple():
    assert Point2D(1, 2).as_tuple() == (1, 2)


def test_immutable():
    p = Point2D(1, 2)
    try:
        p.x = 10
    except Exception:
        return
    raise AssertionError("Point2D deberia ser inmutable")
'''

TEST_VECTOR = '''import math

import pytest

from meshcad.core.geometry.vector import Vector2D


def test_arithmetic():
    a = Vector2D(1, 2)
    b = Vector2D(3, 4)
    assert a + b == Vector2D(4, 6)
    assert b - a == Vector2D(2, 2)
    assert a * 2 == Vector2D(2, 4)
    assert 2 * a == Vector2D(2, 4)
    assert -a == Vector2D(-1, -2)


def test_norm():
    assert math.isclose(Vector2D(3, 4).norm(), 5.0)


def test_normalized():
    v = Vector2D(3, 4).normalized()
    assert math.isclose(v.norm(), 1.0)
    assert math.isclose(v.x, 0.6)
    assert math.isclose(v.y, 0.8)


def test_normalized_zero_raises():
    with pytest.raises(ValueError):
        Vector2D(0, 0).normalized()


def test_dot():
    assert Vector2D(1, 2).dot(Vector2D(3, 4)) == 11


def test_cross():
    assert Vector2D(1, 0).cross(Vector2D(0, 1)) == 1
    assert Vector2D(0, 1).cross(Vector2D(1, 0)) == -1


def test_angle():
    assert math.isclose(Vector2D(1, 0).angle(), 0.0)
    assert math.isclose(Vector2D(0, 1).angle(), math.pi / 2)


def test_rotate_90():
    v = Vector2D(1, 0).rotate(math.pi / 2)
    assert math.isclose(v.x, 0.0, abs_tol=1e-12)
    assert math.isclose(v.y, 1.0, abs_tol=1e-12)
'''


# =========================================================================== #
# COMMIT 2 - GeometryEntity (clase base abstracta)
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
    def sample(self, n: int) -> List[Point2D]:
        """Devuelve n puntos a lo largo de la entidad, incluyendo los extremos.

        n debe ser >= 2.
        """

    @abstractmethod
    def bounding_box(self) -> Tuple[Point2D, Point2D]:
        """Devuelve (min_point, max_point) del rectangulo que la contiene."""
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

        def sample(self, n):
            return [Point2D(0, 0), Point2D(1, 0)]

        def bounding_box(self):
            return (Point2D(0, 0), Point2D(1, 0))

    d = Dummy()
    assert d.length() == 1.0
    assert d.start_point() == Point2D(0, 0)
'''


# =========================================================================== #
# COMMIT 3 - Line
# =========================================================================== #

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

    def sample(self, n: int) -> List[Point2D]:
        if n < 2:
            raise ValueError("n debe ser >= 2")
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        return [
            Point2D(self.start.x + dx * i / (n - 1),
                    self.start.y + dy * i / (n - 1))
            for i in range(n)
        ]

    def bounding_box(self) -> Tuple[Point2D, Point2D]:
        return (
            Point2D(min(self.start.x, self.end.x), min(self.start.y, self.end.y)),
            Point2D(max(self.start.x, self.end.x), max(self.start.y, self.end.y)),
        )
'''

GEOMETRY_INIT_STEP3 = '''"""Entidades geometricas 2D: Point2D, Line, Arc, Spline."""

from meshcad.core.geometry.point import Point2D
from meshcad.core.geometry.vector import Vector2D
from meshcad.core.geometry.entity import GeometryEntity
from meshcad.core.geometry.line import Line

__all__ = ["Point2D", "Vector2D", "GeometryEntity", "Line"]
'''

TEST_LINE = '''import math

import pytest

from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D


def test_start_end():
    line = Line(Point2D(0, 0), Point2D(1, 1))
    assert line.start_point() == Point2D(0, 0)
    assert line.end_point() == Point2D(1, 1)


def test_length():
    line = Line(Point2D(0, 0), Point2D(3, 4))
    assert math.isclose(line.length(), 5.0)


def test_sample_endpoints():
    line = Line(Point2D(0, 0), Point2D(10, 0))
    pts = line.sample(2)
    assert pts == [Point2D(0, 0), Point2D(10, 0)]


def test_sample_middle():
    line = Line(Point2D(0, 0), Point2D(4, 0))
    pts = line.sample(5)
    assert len(pts) == 5
    assert pts[0] == Point2D(0, 0)
    assert pts[-1] == Point2D(4, 0)
    assert math.isclose(pts[2].x, 2.0)


def test_sample_requires_minimum():
    with pytest.raises(ValueError):
        Line(Point2D(0, 0), Point2D(1, 1)).sample(1)


def test_bounding_box():
    line = Line(Point2D(2, 5), Point2D(-1, 0))
    lo, hi = line.bounding_box()
    assert lo == Point2D(-1, 0)
    assert hi == Point2D(2, 5)
'''


# =========================================================================== #
# COMMIT 4 - Arc
# =========================================================================== #

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

    def sample(self, n: int) -> List[Point2D]:
        if n < 2:
            raise ValueError("n debe ser >= 2")
        span = self.angle_span()
        return [
            self.point_at_angle(self.start_angle + span * i / (n - 1))
            for i in range(n)
        ]

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

GEOMETRY_INIT_STEP4 = '''"""Entidades geometricas 2D: Point2D, Line, Arc, Spline."""

from meshcad.core.geometry.point import Point2D
from meshcad.core.geometry.vector import Vector2D
from meshcad.core.geometry.entity import GeometryEntity
from meshcad.core.geometry.line import Line
from meshcad.core.geometry.arc import Arc

__all__ = ["Point2D", "Vector2D", "GeometryEntity", "Line", "Arc"]
'''

TEST_ARC = '''import math

import pytest

from meshcad.core.geometry.arc import Arc
from meshcad.core.geometry.point import Point2D


def make_quarter():
    return Arc(Point2D(0, 0), 1.0, 0.0, math.pi / 2)


def test_negative_radius_raises():
    with pytest.raises(ValueError):
        Arc(Point2D(0, 0), -1.0, 0.0, 1.0)


def test_start_end():
    arc = make_quarter()
    s = arc.start_point()
    e = arc.end_point()
    assert math.isclose(s.x, 1.0)
    assert math.isclose(s.y, 0.0, abs_tol=1e-12)
    assert math.isclose(e.x, 0.0, abs_tol=1e-12)
    assert math.isclose(e.y, 1.0)


def test_length_quarter():
    arc = make_quarter()
    assert math.isclose(arc.length(), math.pi / 2)


def test_length_semicircle():
    arc = Arc(Point2D(0, 0), 2.0, 0.0, math.pi)
    assert math.isclose(arc.length(), 2.0 * math.pi)


def test_span_wraps():
    arc = Arc(Point2D(0, 0), 1.0, math.pi, -math.pi / 2)
    assert math.isclose(arc.angle_span(), 1.5 * math.pi)


def test_sample_count():
    arc = make_quarter()
    assert len(arc.sample(5)) == 5


def test_sample_requires_minimum():
    with pytest.raises(ValueError):
        make_quarter().sample(1)


def test_bounding_box_quarter():
    arc = make_quarter()
    lo, hi = arc.bounding_box()
    assert math.isclose(lo.x, 0.0, abs_tol=1e-12)
    assert math.isclose(lo.y, 0.0, abs_tol=1e-12)
    assert math.isclose(hi.x, 1.0)
    assert math.isclose(hi.y, 1.0)


def test_bounding_box_semicircle_captures_top():
    arc = Arc(Point2D(0, 0), 1.0, 0.0, math.pi)
    lo, hi = arc.bounding_box()
    assert math.isclose(hi.y, 1.0)
'''


# =========================================================================== #
# COMMIT 5 - Spline
# =========================================================================== #

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
        """Evalua la spline en t en [0, 1]."""
        n = len(self.points)
        if n == 2:
            a, b = self.points
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

GEOMETRY_INIT_STEP5 = '''"""Entidades geometricas 2D: Point2D, Line, Arc, Spline."""

from meshcad.core.geometry.point import Point2D
from meshcad.core.geometry.vector import Vector2D
from meshcad.core.geometry.entity import GeometryEntity
from meshcad.core.geometry.line import Line
from meshcad.core.geometry.arc import Arc
from meshcad.core.geometry.spline import Spline

__all__ = [
    "Point2D",
    "Vector2D",
    "GeometryEntity",
    "Line",
    "Arc",
    "Spline",
]
'''

TEST_SPLINE = '''import math

import pytest

from meshcad.core.geometry.point import Point2D
from meshcad.core.geometry.spline import Spline


def test_requires_at_least_two_points():
    with pytest.raises(ValueError):
        Spline((Point2D(0, 0),))


def test_start_end():
    s = Spline((Point2D(0, 0), Point2D(1, 1), Point2D(2, 0)))
    assert s.start_point() == Point2D(0, 0)
    assert s.end_point() == Point2D(2, 0)


def test_interpolates_control_points():
    pts = (Point2D(0, 0), Point2D(1, 2), Point2D(3, 1), Point2D(4, 3))
    s = Spline(pts)
    assert s.evaluate(0.0) == pts[0]
    assert s.evaluate(1.0) == pts[-1]


def test_two_points_is_straight():
    s = Spline((Point2D(0, 0), Point2D(4, 0)))
    mid = s.evaluate(0.5)
    assert math.isclose(mid.x, 2.0)
    assert math.isclose(mid.y, 0.0)


def test_sample_count():
    s = Spline((Point2D(0, 0), Point2D(1, 1), Point2D(2, 0)))
    assert len(s.sample(7)) == 7


def test_sample_requires_minimum():
    with pytest.raises(ValueError):
        Spline((Point2D(0, 0), Point2D(1, 1))).sample(1)


def test_length_is_positive_and_bounded():
    s = Spline((Point2D(0, 0), Point2D(1, 1), Point2D(2, 0)))
    total = s.length()
    assert total > s.start_point().distance_to(s.end_point()) - 1e-9
    assert total < 10.0


def test_bounding_box_contains_all_controls():
    pts = (Point2D(-1, -1), Point2D(0, 3), Point2D(4, 2), Point2D(5, -2))
    lo, hi = Spline(pts).bounding_box()
    for p in pts:
        assert lo.x <= p.x <= hi.x
        assert lo.y <= p.y <= hi.y
'''


# =========================================================================== #
# Ejecucion
# =========================================================================== #

def main():
    check()

    commit(
        "Commit 1/5: Point2D y Vector2D",
        {
            "src/meshcad/core/geometry/point.py": POINT_PY,
            "src/meshcad/core/geometry/vector.py": VECTOR_PY,
            "src/meshcad/core/geometry/__init__.py": GEOMETRY_INIT_STEP1,
            "tests/core/__init__.py": "",
            "tests/core/geometry/__init__.py": "",
            "tests/core/geometry/test_point.py": TEST_POINT,
            "tests/core/geometry/test_vector.py": TEST_VECTOR,
        },
        "feat(core): anadir Point2D y Vector2D",
    )

    commit(
        "Commit 2/5: GeometryEntity (abstracta)",
        {
            "src/meshcad/core/geometry/entity.py": ENTITY_PY,
            "tests/core/geometry/test_entity.py": TEST_ENTITY,
        },
        "feat(core): clase base abstracta GeometryEntity",
    )

    commit(
        "Commit 3/5: Line",
        {
            "src/meshcad/core/geometry/line.py": LINE_PY,
            "src/meshcad/core/geometry/__init__.py": GEOMETRY_INIT_STEP3,
            "tests/core/geometry/test_line.py": TEST_LINE,
        },
        "feat(core): segmento de recta Line",
    )

    commit(
        "Commit 4/5: Arc",
        {
            "src/meshcad/core/geometry/arc.py": ARC_PY,
            "src/meshcad/core/geometry/__init__.py": GEOMETRY_INIT_STEP4,
            "tests/core/geometry/test_arc.py": TEST_ARC,
        },
        "feat(core): arco de circulo Arc",
    )

    commit(
        "Commit 5/5: Spline",
        {
            "src/meshcad/core/geometry/spline.py": SPLINE_PY,
            "src/meshcad/core/geometry/__init__.py": GEOMETRY_INIT_STEP5,
            "tests/core/geometry/test_spline.py": TEST_SPLINE,
        },
        "feat(core): spline interpolante Spline",
    )

    print()
    print("== Historial ==")
    run(["git", "log", "--oneline", "--decorate"])
    print()
    print("Fase 1 completada.")
    print("Verifica con:  python -m pytest")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print()
        print("ERROR:", e)
        sys.exit(1)