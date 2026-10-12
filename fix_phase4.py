#!/usr/bin/env python3
"""
Corrige el test test_split_rejects_foreign_vertex de la fase 4.

El test original creaba otra Topology y asumia que su vertice era
"extranjero", pero Topology asigna IDs desde 0, asi que el ID
coincidia con v0 del cuadrado y el loop lo aceptaba.

El fix usa un ID que no existe en la topologia del loop.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()

TEST_SPLIT_FIXED = '''import math

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


def test_split_rejects_nonexistent_vertex_id():
    # Un ID que no pertenece a la topologia del loop debe ser rechazado.
    t, (v0, _, _, _), _, loop = make_square()
    fake_id = 99999
    with pytest.raises(ValueError):
        loop.split_at_corners(t, [fake_id, 1, 2, 3])


def test_split_with_multiple_edges_per_side():
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

    sides = loop.split_at_corners(
        t, [verts[0].id, verts[2].id, verts[3].id, verts[5].id]
    )
    assert sides[0].edge_ids() == [edges[0].id, edges[1].id]
    assert sides[1].edge_ids() == [edges[2].id]
    assert sides[2].edge_ids() == [edges[3].id, edges[4].id]
    assert sides[3].edge_ids() == [edges[5].id]
'''


def run(cmd):
    print("  $ " + " ".join(cmd))
    r = subprocess.run(cmd, cwd=str(ROOT))
    if r.returncode != 0:
        raise RuntimeError("Fallo: " + " ".join(cmd))


def main():
    target = ROOT / "tests" / "core" / "topology" / "test_split.py"
    if not target.exists():
        print("ERROR: no existe " + str(target))
        sys.exit(1)

    print("== Corrigiendo " + str(target.relative_to(ROOT)) + " ==")
    target.write_text(TEST_SPLIT_FIXED, encoding="utf-8")

    print("== Verificando tests ==")
    run([sys.executable, "-m", "pytest", "-q"])

    print("== Creando commit ==")
    run(["git", "add", str(target.relative_to(ROOT))])
    run([
        "git", "commit", "-m",
        "fix(test): usar ID inexistente para vertice extranjero en split",
    ])

    print()
    print("== Historial ==")
    run(["git", "log", "--oneline"])


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print()
        print("ERROR:", e)
        sys.exit(1)