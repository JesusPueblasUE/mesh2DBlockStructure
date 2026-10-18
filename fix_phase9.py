#!/usr/bin/env python3
"""
Corrige los errores introducidos en la Fase 9.
1. Restaura validaciones y metodos dunder en Topology.
2. Actualiza el test Dummy para implementar get_grips.
3. Corrige el indice en el test de auto-mesh.
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
    print("== Corrigiendo Topology ==")
    
    # 1. Restaurar validacion en add_edge
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
            raise ValueError(
                "El punto inicial de la geometria no coincide con start_vertex"
            )
        if geometry.end_point().distance_to(end_vertex.point) > TOL:
            raise ValueError(
                "El punto final de la geometria no coincide con end_vertex"
            )
        e = Edge(next(self._edge_ids), start_vertex.id, end_vertex.id, geometry)
        self._edges[e.id] = e
        return e'''
        
    patch_file("src/meshcad/core/topology/topology.py", old_add_edge, new_add_edge)

    # 2. Restaurar __len__ y __repr__ (anadiendolos al final de la clase)
    old_import = '''    def import_state(self, vertices: Dict[int, Vertex], edges: Dict[int, Edge]) -> None:
        from itertools import count as _count
        self._vertices = dict(vertices)
        self._edges = dict(edges)
        max_v = max(self._vertices.keys(), default=-1)
        max_e = max(self._edges.keys(), default=-1)
        self._vertex_ids = _count(max_v + 1)
        self._edge_ids = _count(max_e + 1)'''
        
    new_import = '''    def import_state(self, vertices: Dict[int, Vertex], edges: Dict[int, Edge]) -> None:
        from itertools import count as _count
        self._vertices = dict(vertices)
        self._edges = dict(edges)
        max_v = max(self._vertices.keys(), default=-1)
        max_e = max(self._edges.keys(), default=-1)
        self._vertex_ids = _count(max_v + 1)
        self._edge_ids = _count(max_e + 1)

    def __len__(self) -> int:
        return len(self._vertices) + len(self._edges)

    def __repr__(self) -> str:
        return "Topology(vertices={}, edges={})".format(
            len(self._vertices), len(self._edges)
        )'''
        
    patch_file("src/meshcad/core/topology/topology.py", old_import, new_import)

    print("== Corrigiendo tests ==")
    
    # 3. test_entity.py
    old_dummy = '''    class Dummy(GeometryEntity):
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
            return (Point2D(0, 0), Point2D(1, 0))'''
            
    new_dummy = '''    class Dummy(GeometryEntity):
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
            
        def get_grips(self):
            return []'''
            
    patch_file("tests/core/geometry/test_entity.py", old_dummy, new_dummy)

    # 4. test_canvas_drag.py
    patch_file(
        "tests/gui/test_canvas_drag.py",
        "assert new_mesh.grid[0][1].x == 2.0",
        "assert new_mesh.grid[0][-1].x == 2.0"
    )

    print()
    print("== Verificando tests ==")
    run([sys.executable, "-m", "pytest", "-q"])

    print()
    print("== Creando commit ==")
    run(["git", "add", "."])
    run([
        "git", "commit", "-m",
        "fix(core): restaurar validaciones y metodos dunder en Topology, corregir tests",
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