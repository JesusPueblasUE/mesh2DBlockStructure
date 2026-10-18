#!/usr/bin/env python3
"""
Corrige los tests que fallaban porque la propagacion de nodos impedia
crear un desajuste usando set_edge_spec. Ahora se inyecta directo en mesh.set_spec.
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


def patch_file(rel_path, old, new):
    p = ROOT / rel_path
    content = p.read_text(encoding="utf-8")
    if old not in content:
        print("ERROR: no se encuentra el patron en " + rel_path)
        sys.exit(1)
    content = content.replace(old, new)
    p.write_text(content, encoding="utf-8")
    print("  ~ " + rel_path)


def main():
    print("== Corrigiendo tests de desajuste (propagacion) ==")

    # 1. test_blocks_panel.py
    old_panel = '''    doc.blocks.append(block)
    doc.set_edge_spec(EdgeMeshSpec(0, 5, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(1, 6, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(2, 8, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(3, 6, UniformDistribution()))

    panel = BlocksPanel(doc)'''

    new_panel = '''    doc.blocks.append(block)
    doc.mesh.set_spec(EdgeMeshSpec(0, 5, UniformDistribution()))
    doc.mesh.set_spec(EdgeMeshSpec(1, 6, UniformDistribution()))
    doc.mesh.set_spec(EdgeMeshSpec(2, 8, UniformDistribution()))
    doc.mesh.set_spec(EdgeMeshSpec(3, 6, UniformDistribution()))
    doc.recompute_blocks()

    panel = BlocksPanel(doc)'''
    
    patch_file("tests/gui/test_blocks_panel.py", old_panel, new_panel)

    # 2. test_document.py
    old_doc = '''    # Desajuste lados 0/2
    doc.set_edge_spec(EdgeMeshSpec(e0.id, 4, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(e2.id, 6, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(e1.id, 4, UniformDistribution()))
    doc.set_edge_spec(EdgeMeshSpec(e3.id, 4, UniformDistribution()))

    meshes, errors = doc.generate_mesh()'''

    new_doc = '''    # Desajuste lados 0/2 (inyectado directamente para saltar la propagacion)
    doc.mesh.set_spec(EdgeMeshSpec(e0.id, 4, UniformDistribution()))
    doc.mesh.set_spec(EdgeMeshSpec(e2.id, 6, UniformDistribution()))
    doc.mesh.set_spec(EdgeMeshSpec(e1.id, 4, UniformDistribution()))
    doc.mesh.set_spec(EdgeMeshSpec(e3.id, 4, UniformDistribution()))
    doc.recompute_blocks()

    meshes, errors = doc.generate_mesh()'''
    
    patch_file("tests/gui/test_document.py", old_doc, new_doc)

    print("\n== Verificando tests ==")
    run([sys.executable, "-m", "pytest", "-q"])

    print("\n== Creando commit ==")
    run(["git", "add", "."])
    run([
        "git", "commit", "-m",
        "fix(test): inyectar desajuste directo en mesh.set_spec por la propagacion",
    ])


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print("\nERROR:", e)
        sys.exit(1)