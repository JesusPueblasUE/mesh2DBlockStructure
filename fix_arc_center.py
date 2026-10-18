#!/usr/bin/env python3
"""
Corrige el comportamiento al arrastrar el centro (grip) de un arco.

Ahora, al mover el centro, los extremos se quedan fijos y el centro
se proyecta sobre la mediatriz de los extremos, cambiando el radio.
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
    print("== Corrigiendo el arrastre del centro de arcos ==")

    old_grip_logic = '''        if isinstance(g, Arc) and grip_index == 0:
            delta = Vector2D(new_point.x - g.center.x, new_point.y - g.center.y)
            v_start = self._vertices[edge.start_vertex_id].point + delta
            v_end = self._vertices[edge.end_vertex_id].point + delta
            self._vertices[edge.start_vertex_id] = Vertex(edge.start_vertex_id, v_start)
            self._vertices[edge.end_vertex_id] = Vertex(edge.end_vertex_id, v_end)

            new_g = Arc(new_point, g.radius, g.start_angle, g.end_angle)
            self._edges[edge_id] = Edge(edge_id, edge.start_vertex_id, edge.end_vertex_id, new_g)'''

    new_grip_logic = '''        if isinstance(g, Arc) and grip_index == 0:
            v_start = self._vertices[edge.start_vertex_id].point
            v_end = self._vertices[edge.end_vertex_id].point
            
            # Proyectar el nuevo centro sobre la mediatriz de v_start y v_end
            mx = (v_start.x + v_end.x) / 2.0
            my = (v_start.y + v_end.y) / 2.0
            dx = v_end.x - v_start.x
            dy = v_end.y - v_start.y
            
            nx, ny = -dy, dx
            norm = math.hypot(nx, ny)
            if norm > 1e-9:
                nx /= norm
                ny /= norm
                # Proyeccion escalar del punto del raton sobre el vector normal
                t = (new_point.x - mx) * nx + (new_point.y - my) * ny
                new_center = Point2D(mx + t * nx, my + t * ny)
            else:
                new_center = new_point

            # El radio es la distancia desde el nuevo centro a un extremo
            r = new_center.distance_to(v_start)
            a0 = math.atan2(v_start.y - new_center.y, v_start.x - new_center.x)
            a1 = math.atan2(v_end.y - new_center.y, v_end.x - new_center.x)
            
            new_g = Arc(new_center, max(r, 1e-6), a0, a1)
            self._edges[edge_id] = Edge(edge_id, edge.start_vertex_id, edge.end_vertex_id, new_g)'''

    patch_file("src/meshcad/core/topology/topology.py", old_grip_logic, new_grip_logic)

    print("\n== Anadiendo test para el nuevo comportamiento ==")
    
    test_file = ROOT / "tests" / "core" / "topology" / "test_grips.py"
    content = test_file.read_text(encoding="utf-8")
    
    old_test = '''def test_move_arc_center_translates():'''
    new_test = '''def test_move_arc_center_changes_radius():
    t = Topology()
    v0 = t.add_vertex(Point2D(1, 0))
    v1 = t.add_vertex(Point2D(-1, 0))
    arc = Arc(Point2D(0, 0), 1.0, 0.0, math.pi)
    e = t.add_edge(v0, v1, arc)

    # Movemos el centro a (0, 1). Debe quedarse en (0, 1)
    t.move_edge_grip(e.id, 0, Point2D(0, 1))
    new_arc = t.get_edge(e.id).geometry
    
    # Los extremos NO deben moverse
    assert t.get_vertex(v0.id).point == Point2D(1, 0)
    assert t.get_vertex(v1.id).point == Point2D(-1, 0)
    
    assert isinstance(new_arc, Arc)
    assert math.isclose(new_arc.center.x, 0.0)
    assert math.isclose(new_arc.center.y, 1.0)
    assert math.isclose(new_arc.radius, math.sqrt(2))

def test_move_arc_center_translates():'''
    
    content = content.replace(old_test, new_test)
    test_file.write_text(content, encoding="utf-8")
    print("  ~ tests/core/topology/test_grips.py")

    print("\n== Verificando tests ==")
    run([sys.executable, "-m", "pytest", "-q"])

    print("\n== Creando commit ==")
    run(["git", "add", "."])
    run([
        "git", "commit", "-m",
        "fix(core): proyectar centro de arco sobre la mediatriz al mover grip",
    ])


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print("\nERROR:", e)
        sys.exit(1)