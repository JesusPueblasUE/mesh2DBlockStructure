#!/usr/bin/env python3
"""
Corrige el arco del test make_square_topology en la fase 7.

El arco original no empezaba en v2=(1,1) ni terminaba en v3=(0,1),
asi que add_edge lo rechazaba correctamente. El arco correcto tiene
centro (0.5, 1), radio 0.5, start_angle=0, end_angle=pi.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()


def run(cmd):
    print("  $ " + " ".join(cmd))
    r = subprocess.run(cmd, cwd=str(ROOT))
    if r.returncode != 0:
        raise RuntimeError("Fallo: " + " ".join(cmd))


def main():
    target = ROOT / "tests" / "io" / "test_json_topology.py"
    if not target.exists():
        print("ERROR: no existe " + str(target))
        sys.exit(1)

    content = target.read_text(encoding="utf-8")

    old = "t.add_edge(v2, v3, Arc(Point2D(0.5, 0.5), 0.5, math.pi / 2, math.pi))"
    new = "t.add_edge(v2, v3, Arc(Point2D(0.5, 1.0), 0.5, 0.0, math.pi))"

    if old not in content:
        print("ERROR: no encuentro la linea a sustituir.")
        print("Contenido actual del fichero (primeras lineas):")
        print("\n".join(content.splitlines()[:40]))
        sys.exit(1)

    content = content.replace(old, new)
    target.write_text(content, encoding="utf-8")
    print("  + " + str(target.relative_to(ROOT)) + " corregido")

    print()
    print("== Verificando tests ==")
    run([sys.executable, "-m", "pytest", "-q"])

    print()
    print("== Creando commit ==")
    run(["git", "add", str(target.relative_to(ROOT))])
    run([
        "git", "commit", "-m",
        "fix(test): arco coherente con sus vertices en make_square_topology",
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