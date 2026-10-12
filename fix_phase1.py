#!/usr/bin/env python3
"""
Corrige la expectativa del test test_span_wraps en la fase 1.

El test original asumia que Arc(pi -> -pi/2) barre 1.5*pi, pero en
convenio CCW el barrido real es pi/2. Se anade ademas un caso
que si barre 1.5*pi.

Uso:
    cd meshcad
    python fix_phase1.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()


TEST_ARC_FIXED = '''import math

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


def test_span_wraps_short():
    # CCW desde pi hasta -pi/2 (= 3pi/2) recorre pi/2
    arc = Arc(Point2D(0, 0), 1.0, math.pi, -math.pi / 2)
    assert math.isclose(arc.angle_span(), math.pi / 2)


def test_span_wraps_long():
    # CCW desde -pi/2 hasta pi recorre 1.5*pi
    arc = Arc(Point2D(0, 0), 1.0, -math.pi / 2, math.pi)
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


def run(cmd):
    print("  $ " + " ".join(cmd))
    r = subprocess.run(cmd, cwd=str(ROOT))
    if r.returncode != 0:
        raise RuntimeError("Fallo: " + " ".join(cmd))


def main():
    if not (ROOT / "pyproject.toml").exists():
        print("ERROR: ejecuta este script desde la raiz del proyecto meshcad.")
        sys.exit(1)

    target = ROOT / "tests" / "core" / "geometry" / "test_arc.py"
    if not target.exists():
        print("ERROR: no existe " + str(target))
        sys.exit(1)

    print("== Corrigiendo " + str(target.relative_to(ROOT)) + " ==")
    target.write_text(TEST_ARC_FIXED, encoding="utf-8")

    print("== Verificando tests ==")
    run([sys.executable, "-m", "pytest", "-q"])

    print("== Creando commit ==")
    run(["git", "add", str(target.relative_to(ROOT))])
    run([
        "git", "commit", "-m",
        "fix(test): corregir expectativa de span CCW en Arc",
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