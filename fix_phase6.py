#!/usr/bin/env python3
"""
Corrige el test test_adjacent_blocks_are_conformal de la fase 6.

El loop izquierdo tenia dos aristas marcadas como reversed que no
debian estarlo. e_top_left (v2->v3) y e_left (v3->v0) ya van en el
sentido correcto del loop, asi que no hay que invertirlas.
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
    target = ROOT / "tests" / "core" / "mesh" / "test_generator.py"
    if not target.exists():
        print("ERROR: no existe " + str(target))
        sys.exit(1)

    content = target.read_text(encoding="utf-8")

    old_block = '''    loop_left = Loop()
    loop_left.add_edge(e_bottom_left.id)
    loop_left.add_edge(e_shared.id)
    loop_left.add_edge(e_top_left.id, reversed=True)
    loop_left.add_edge(e_left.id, reversed=True)'''

    new_block = '''    loop_left = Loop()
    loop_left.add_edge(e_bottom_left.id)
    loop_left.add_edge(e_shared.id)
    loop_left.add_edge(e_top_left.id)
    loop_left.add_edge(e_left.id)'''

    if old_block not in content:
        print("ERROR: no encontrado el bloque a sustituir.")
        print("Revisa el fichero a mano.")
        sys.exit(1)

    content = content.replace(old_block, new_block)
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
        "fix(test): quitar reversed incorrecto en loop izquierdo del test de conformidad",
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