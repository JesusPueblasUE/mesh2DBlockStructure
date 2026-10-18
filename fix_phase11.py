#!/usr/bin/env python3
"""
Restaura la validacion de geometria en Topology.add_edge.
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
        print("--- buscado ---")
        print(old)
        sys.exit(1)
    content = content.replace(old, new)
    p.write_text(content, encoding="utf-8")
    print("  ~ " + rel_path)


def main():
    print("== Restaurando validacion en add_edge ==")

    old_add_edge = '''    def add_edge(self, start_vertex: Vertex, end_vertex: Vertex,
                 geometry: GeometryEntity) -> Edge:
        if not self.has_vertex(start_vertex.id) or not self.has_vertex(end_vertex.id):
            raise ValueError("vertices extranjeros")
        e = Edge(next(self._edge_ids), start_vertex.id, end_vertex.id, geometry)
        self._edges[e.id] = e
        return e'''

    new_add_edge = '''    def add_edge(self, start_vertex: Vertex, end_vertex: Vertex,
                 geometry: GeometryEntity) -> Edge:
        if not self.has_vertex(start_vertex.id):
            raise ValueError("start_vertex no pertenece a esta topologia")
        if not self.has_vertex(end_vertex.id):
            raise ValueError("end_vertex no pertenece a esta topologia")
        if geometry.start_point().distance_to(start_vertex.point) > TOL:
            raise ValueError("El punto inicial de la geometria no coincide con start_vertex")
        if geometry.end_point().distance_to(end_vertex.point) > TOL:
            raise ValueError("El punto final de la geometria no coincide con end_vertex")
            
        e = Edge(next(self._edge_ids), start_vertex.id, end_vertex.id, geometry)
        self._edges[e.id] = e
        return e'''

    patch_file("src/meshcad/core/topology/topology.py", old_add_edge, new_add_edge)

    print("\n== Verificando tests ==")
    run([sys.executable, "-m", "pytest", "-q"])

    print("\n== Creando commit ==")
    run(["git", "add", "."])
    run([
        "git", "commit", "-m",
        "fix(core): restaurar validacion de geometria en Topology.add_edge",
    ])


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print("\nERROR:", e)
        sys.exit(1)