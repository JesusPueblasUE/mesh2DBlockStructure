#!/usr/bin/env python3
"""
Corrige el error al borrar multiples aristas:
1. Procesa el borrado en lote para no destruir la lista durante la iteracion.
2. Limpia el resaltado del canvas al borrar.
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
    print("== Actualizando Document para borrado en lote ==")

    old_doc = '''    def remove_edge(self, edge_id: int) -> bool:
        for b in self.blocks:
            for side in b.sides:
                if edge_id in side.edge_ids():
                    return False
        
        self.topology.remove_edge(edge_id)
        self.mesh.clear_spec(edge_id)
        self.notify_change()
        return True'''

    new_doc = '''    def remove_edges(self, edge_ids: list) -> tuple:
        success = 0
        fail = 0
        for eid in edge_ids:
            in_block = False
            for b in self.blocks:
                for side in b.sides:
                    if eid in side.edge_ids():
                        in_block = True
                        break
                if in_block:
                    break
            
            if in_block:
                fail += 1
            else:
                self.topology.remove_edge(eid)
                self.mesh.clear_spec(eid)
                success += 1
                
        if success > 0:
            self.notify_change()
        return success, fail'''

    patch_file("src/meshcad/gui/document.py", old_doc, new_doc)

    print("== Actualizando EdgesPanel para usar el borrado en lote ==")
    
    old_panel = '''    def _on_delete(self) -> None:
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return
            
        edges = self.document.topology.edges()
        success = 0
        fail = 0
        for item in selected_items:
            row = self.list_widget.row(item)
            if 0 <= row < len(edges):
                if self.document.remove_edge(edges[row].id):
                    success += 1
                else:
                    fail += 1
        self.refresh()
        if fail > 0:
            self.status.setText("{} aristas borradas. {} no se pudieron borrar porque pertenecen a un bloque.".format(success, fail))
        else:
            self.status.setText("{} aristas borradas.".format(success))'''

    new_panel = '''    def _on_delete(self) -> None:
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return
            
        edges = self.document.topology.edges()
        edge_ids_to_delete = []
        for item in selected_items:
            row = self.list_widget.row(item)
            if 0 <= row < len(edges):
                edge_ids_to_delete.append(edges[row].id)
                
        self.canvas.clear_highlight()

        success, fail = self.document.remove_edges(edge_ids_to_delete)
        self.refresh()
        
        if fail > 0:
            self.status.setText("{} aristas borradas. {} no se pudieron borrar porque pertenecen a un bloque.".format(success, fail))
        else:
            self.status.setText("{} aristas borradas.".format(success))'''

    patch_file("src/meshcad/gui/edges_panel.py", old_panel, new_panel)

    print("\n== Verificando tests ==")
    run([sys.executable, "-m", "pytest", "-q"])

    print("\n== Creando commit ==")
    run(["git", "add", "."])
    run([
        "git", "commit", "-m",
        "fix(gui): borrado de aristas en lote y limpieza de resaltado",
    ])


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print("\nERROR:", e)
        sys.exit(1)