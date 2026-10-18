#!/usr/bin/env python3
"""
Fix: Eliminar vertices huerfanos al borrar una arista.
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
    print("== Modificando Topology.remove_edge ==")

    old_remove = '''    def remove_edge(self, edge_id: int) -> None:
        if edge_id in self._edges:
            del self._edges[edge_id]'''

    new_remove = '''    def remove_edge(self, edge_id: int) -> None:
        if edge_id not in self._edges:
            return
            
        edge = self._edges.pop(edge_id)
        
        # Comprobar si los vertices han quedado huerfanos (sin otras aristas)
        used_vertices = set()
        for e in self._edges.values():
            used_vertices.add(e.start_vertex_id)
            used_vertices.add(e.end_vertex_id)
            
        if edge.start_vertex_id not in used_vertices:
            self._vertices.pop(edge.start_vertex_id, None)
            
        if edge.end_vertex_id not in used_vertices:
            self._vertices.pop(edge.end_vertex_id, None)'''

    patch_file("src/meshcad/core/topology/topology.py", old_remove, new_remove)

    # Añadir test de verificacion
    print("\n== Añadiendo test de verificacion ==")
    test_content = '''from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.core.topology.topology import Topology


def test_remove_edge_deletes_orphaned_vertices():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    e = t.add_edge(v0, v1, Line(v0.point, v1.point))
    
    assert len(t.vertices()) == 2
    t.remove_edge(e.id)
    assert len(t.edges()) == 0
    assert len(t.vertices()) == 0


def test_remove_edge_keeps_shared_vertices():
    t = Topology()
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    v2 = t.add_vertex(Point2D(2, 0))
    e0 = t.add_edge(v0, v1, Line(v0.point, v1.point))
    e1 = t.add_edge(v1, v2, Line(v1.point, v2.point))
    
    assert len(t.vertices()) == 3
    t.remove_edge(e0.id)
    assert len(t.edges()) == 1
    
    # v1 sigue en uso por e1, asi que no debe borrarse. v0 si debe borrarse.
    v_ids = [v.id for v in t.vertices()]
    assert v0.id not in v_ids
    assert v1.id in v_ids
    assert v2.id in v_ids
'''
    p = ROOT / "tests" / "core" / "topology" / "test_remove_edge.py"
    p.write_text(test_content, encoding="utf-8")
    print("  + tests/core/topology/test_remove_edge.py")

    print("\n== Verificando tests ==")
    run([sys.executable, "-m", "pytest", "-q"])

    print("\n== Creando commit ==")
    run(["git", "add", "."])
    run([
        "git", "commit", "-m",
        "fix(core): eliminar vertices huerfanos al borrar aristas",
    ])


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print("\nERROR:", e)
        sys.exit(1)