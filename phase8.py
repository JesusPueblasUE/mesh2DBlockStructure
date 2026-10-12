#!/usr/bin/env python3
"""
Fase 8 del proyecto MeshCAD: consolidacion final.

Contenido:
  - commit 39: refactor(core) Topology.import_state
  - commit 40: refactor(io)   project_io puro sobre dict
  - commit 41: refactor(gui)  main_window usa to_dict/from_dict
  - commit 42: docs           manual de usuario y arquitectura
  - commit 43: chore          ruff + mypy
  - commit 44: ci             GitHub Actions
  - commit 45: chore          PyInstaller + tag v1.0.0

Uso:
    cd meshcad
    python phase8.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #

def check():
    if not (ROOT / "pyproject.toml").exists():
        print("ERROR: ejecuta este script desde la raiz del proyecto meshcad.")
        sys.exit(1)
    if not (ROOT / ".git").exists():
        print("ERROR: este directorio no es un repositorio git.")
        sys.exit(1)


def run(cmd, check_only=False):
    print("  $ " + " ".join(cmd))
    r = subprocess.run(cmd, cwd=str(ROOT))
    if r.returncode != 0 and not check_only:
        raise RuntimeError("Fallo: " + " ".join(cmd))
    return r.returncode


def write(rel, content):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print("  + " + rel)


def replace_in_file(rel, old, new, expected_count=1):
    p = ROOT / rel
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected_count:
        print("ERROR: en " + rel + " esperaba " + str(expected_count) +
              " ocurrencias del patron, encontre " + str(count))
        print("--- patron buscado ---")
        print(old)
        print("----------------------")
        sys.exit(1)
    text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")
    print("  ~ " + rel)


def commit(stage, files, msg):
    print()
    print("== " + stage + " ==")
    for rel, content in files.items():
        write(rel, content)
    run(["git", "add", "."])
    run(["git", "commit", "-m", msg])


def commit_patched(stage, msg):
    print()
    print("== " + stage + " ==")
    run(["git", "add", "."])
    run(["git", "commit", "-m", msg])


# --------------------------------------------------------------------------- #
# COMMIT 39 - refactor(core): Topology.import_state
# --------------------------------------------------------------------------- #

def do_commit_39():
    print()
    print("== Commit 39: refactor(core) Topology.import_state ==")

    replace_in_file(
        "src/meshcad/core/topology/topology.py",
        '    def _load_state(self, vertices, edges) -> None:\n'
        '        """Reemplaza el estado interno (uso: deserializacion)."""',
        '    def import_state(self, vertices, edges) -> None:\n'
        '        """Reemplaza el estado interno desde diccionarios externos.\n'
        '\n'
        '        API publica usada por la capa de IO. Recalcula los\n'
        '        contadores para que los siguientes add_vertex/add_edge\n'
        '        sigan asignando IDs unicos.\n'
        '        """',
    )

    replace_in_file(
        "src/meshcad/io/json_io.py",
        "    t._load_state(vertices, edges)",
        "    t.import_state(vertices, edges)",
    )

    commit_patched(
        "Commit 39",
        "refactor(core): exponer Topology.import_state como API publica",
    )


# --------------------------------------------------------------------------- #
# COMMIT 40 - refactor(io): project_io puro sobre dict
# --------------------------------------------------------------------------- #

PROJECT_IO_PY = '''"""Guardar y cargar proyectos en formato JSON (puro dict).

Este modulo NO depende de la GUI: recibe y devuelve diccionarios.
La conversion dict <-> Document vive en la capa de GUI, que es la
unica que conoce Qt. Asi `meshcad.io` se puede importar sin tener
PyQt5 instalado.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def save_project(data: Dict[str, Any], path) -> None:
    """Escribe un proyecto serializado en disco como JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_project(path) -> Dict[str, Any]:
    """Lee un proyecto desde disco y devuelve su diccionario."""
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8"))
'''

IO_INIT_PY = '''"""Persistencia (JSON) y exportacion (VTK).

Este paquete NO depende de PyQt5. La conversion dict <-> Document
vive en la capa de GUI.
"""

from meshcad.io.json_io import (
    block_from_dict,
    block_side_from_dict,
    block_side_to_dict,
    block_to_dict,
    distribution_from_dict,
    distribution_to_dict,
    edge_spec_from_dict,
    edge_spec_to_dict,
    geometry_from_dict,
    geometry_to_dict,
    topology_from_dict,
    topology_to_dict,
)
from meshcad.io.project_io import load_project, save_project
from meshcad.io.vtk_io import export_mesh_vtk

__all__ = [
    "geometry_to_dict",
    "geometry_from_dict",
    "distribution_to_dict",
    "distribution_from_dict",
    "topology_to_dict",
    "topology_from_dict",
    "edge_spec_to_dict",
    "edge_spec_from_dict",
    "block_side_to_dict",
    "block_side_from_dict",
    "block_to_dict",
    "block_from_dict",
    "save_project",
    "load_project",
    "export_mesh_vtk",
]
'''

TEST_PROJECT_IO = '''"""La capa io solo trata con dicts; no importa Qt."""

import sys


def test_io_package_does_not_import_qt():
    """Importar meshcad.io no debe arrastrar PyQt5."""
    for name in list(sys.modules):
        if name.startswith("PyQt5") or name.startswith("meshcad.gui"):
            del sys.modules[name]

    import meshcad.io  # noqa: F401

    assert "meshcad.gui" not in sys.modules
    assert "meshcad.gui.document" not in sys.modules


def test_save_and_load_round_trip(tmp_path):
    from meshcad.io.project_io import load_project, save_project

    data = {
        "format": "meshcad-project",
        "version": 1,
        "payload": {"a": 1, "b": [2, 3]},
    }
    path = tmp_path / "p.json"
    save_project(data, path)
    assert path.exists()
    back = load_project(path)
    assert back == data


def test_save_creates_parent_dirs(tmp_path):
    from meshcad.io.project_io import save_project

    path = tmp_path / "a" / "b" / "p.json"
    save_project({"k": "v"}, path)
    assert path.exists()
'''


def do_commit_40():
    commit(
        "Commit 40: refactor(io) project_io puro sobre dict",
        {
            "src/meshcad/io/project_io.py": PROJECT_IO_PY,
            "src/meshcad/io/__init__.py": IO_INIT_PY,
            "tests/io/test_project_io.py": TEST_PROJECT_IO,
        },
        "refactor(io): project_io puro sobre dict sin depender de gui",
    )


# --------------------------------------------------------------------------- #
# COMMIT 41 - refactor(gui): main_window usa to_dict/from_dict
# --------------------------------------------------------------------------- #

MAIN_WINDOW_PY = '''"""Ventana principal de MeshCAD."""

import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QToolBar,
)

from meshcad.gui.blocks_panel import BlocksPanel
from meshcad.gui.canvas import CadCanvas
from meshcad.gui.document import Document
from meshcad.gui.edges_panel import EdgesPanel
from meshcad.gui.loops_panel import LoopsPanel
from meshcad.gui.tools.arc_tool import ArcTool
from meshcad.gui.tools.line_tool import LineTool
from meshcad.gui.tools.spline_tool import SplineTool
from meshcad.io.project_io import load_project, save_project


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MeshCAD - sin titulo")
        self.resize(1400, 800)

        self.document = Document()
        self.current_path = None

        self.canvas = CadCanvas(self.document)
        self.setCentralWidget(self.canvas)

        self.loops_panel = LoopsPanel(self.document, self.canvas, self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.loops_panel)

        self.edges_panel = EdgesPanel(self.document, self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.edges_panel)

        self.blocks_panel = BlocksPanel(self.document, self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.blocks_panel)

        self.document.topology_changed.connect(self.edges_panel.refresh)
        self.document.project_replaced.connect(self._on_project_replaced)

        status = QStatusBar()
        self.setStatusBar(status)
        self.status_label = QLabel("Listo")
        status.addWidget(self.status_label)

        self._create_menus()
        self._create_toolbar()

    # ------------------------------ menus ------------------------------- #

    def _create_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&Archivo")

        self.action_new = QAction("Nuevo", self)
        self.action_new.setShortcut("Ctrl+N")
        self.action_new.triggered.connect(self._on_new)
        file_menu.addAction(self.action_new)

        self.action_open = QAction("Abrir...", self)
        self.action_open.setShortcut("Ctrl+O")
        self.action_open.triggered.connect(self._on_open)
        file_menu.addAction(self.action_open)

        file_menu.addSeparator()

        self.action_save = QAction("Guardar", self)
        self.action_save.setShortcut("Ctrl+S")
        self.action_save.triggered.connect(self._on_save)
        file_menu.addAction(self.action_save)

        self.action_save_as = QAction("Guardar como...", self)
        self.action_save_as.setShortcut("Ctrl+Shift+S")
        self.action_save_as.triggered.connect(self._on_save_as)
        file_menu.addAction(self.action_save_as)

        file_menu.addSeparator()

        self.action_export_vtk = QAction("Exportar malla (VTK)...", self)
        self.action_export_vtk.triggered.connect(self._on_export_vtk)
        file_menu.addAction(self.action_export_vtk)

        file_menu.addSeparator()

        self.action_quit = QAction("Salir", self)
        self.action_quit.setShortcut("Ctrl+Q")
        self.action_quit.triggered.connect(self.close)
        file_menu.addAction(self.action_quit)

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("Herramientas", self)
        self.addToolBar(toolbar)

        self.action_select = QAction("Seleccionar", self)
        self.action_select.triggered.connect(lambda: self.canvas.set_tool(None))
        toolbar.addAction(self.action_select)

        self.action_line = QAction("Linea", self)
        self.action_line.triggered.connect(
            lambda: self.canvas.set_tool(LineTool(self.canvas))
        )
        toolbar.addAction(self.action_line)

        self.action_arc = QAction("Arco", self)
        self.action_arc.triggered.connect(
            lambda: self.canvas.set_tool(ArcTool(self.canvas))
        )
        toolbar.addAction(self.action_arc)

        self.action_spline = QAction("Spline", self)
        self.action_spline.triggered.connect(
            lambda: self.canvas.set_tool(SplineTool(self.canvas))
        )
        toolbar.addAction(self.action_spline)

        toolbar.addSeparator()

        self.action_mesh = QAction("Generar malla", self)
        self.action_mesh.triggered.connect(self._on_generate_mesh)
        toolbar.addAction(self.action_mesh)

        self.action_clear_mesh = QAction("Borrar malla", self)
        self.action_clear_mesh.triggered.connect(self.canvas.clear_mesh)
        toolbar.addAction(self.action_clear_mesh)

    # ---------------------------- file slots ---------------------------- #

    def _on_new(self) -> None:
        self.document.load_from(Document())
        self.current_path = None
        self.canvas.clear_mesh()
        self.canvas.clear_highlight()
        self._update_title()
        self.status_label.setText("Proyecto nuevo.")

    def _on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir proyecto", "", "MeshCAD (*.json);;Todos (*)"
        )
        if not path:
            return
        try:
            data = load_project(path)
            loaded = Document.from_dict(data)
        except Exception as e:
            QMessageBox.critical(self, "Error al abrir", str(e))
            return
        self.document.load_from(loaded)
        self.current_path = Path(path)
        self.canvas.clear_mesh()
        self._update_title()
        self.status_label.setText("Proyecto cargado: {}".format(path))

    def _on_save(self) -> None:
        if self.current_path is None:
            self._on_save_as()
            return
        self._save_to(self.current_path)

    def _on_save_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar proyecto como", "proyecto.json",
            "MeshCAD (*.json);;Todos (*)"
        )
        if not path:
            return
        self._save_to(Path(path))

    def _save_to(self, path: Path) -> None:
        try:
            save_project(self.document.to_dict(), path)
        except Exception as e:
            QMessageBox.critical(self, "Error al guardar", str(e))
            return
        self.current_path = path
        self._update_title()
        self.status_label.setText("Guardado en: {}".format(path))

    def _on_export_vtk(self) -> None:
        if not self.document.block_meshes:
            QMessageBox.information(
                self, "Sin malla",
                "Genera primero la malla con el boton 'Generar malla'."
            )
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar malla VTK", "malla.pvd",
            "ParaView Data (*.pvd);;Todos (*)"
        )
        if not path:
            return
        try:
            from meshcad.io.vtk_io import export_mesh_vtk
            export_mesh_vtk(self.document.block_meshes, path)
        except Exception as e:
            QMessageBox.critical(self, "Error al exportar", str(e))
            return
        self.status_label.setText("Malla exportada a: {}".format(path))

    # ------------------------------ helpers ----------------------------- #

    def _update_title(self) -> None:
        if self.current_path is None:
            self.setWindowTitle("MeshCAD - sin titulo")
        else:
            self.setWindowTitle("MeshCAD - {}".format(self.current_path))

    def _on_project_replaced(self) -> None:
        self.edges_panel.refresh()

    def _on_generate_mesh(self) -> None:
        meshes, errors = self.document.generate_mesh()
        if errors:
            self.status_label.setText("Errores: " + "; ".join(errors))
        else:
            total_cells = sum(bm.cell_count() for bm in meshes)
            self.status_label.setText(
                "Malla generada: {} bloques, {} celdas".format(
                    len(meshes), total_cells
                )
            )


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
'''

TEST_MAIN_WINDOW = '''from meshcad.core.geometry.line import Line
from meshcad.core.geometry.point import Point2D
from meshcad.gui.document import Document
from meshcad.gui.main_window import MainWindow
from meshcad.io.project_io import load_project


def test_main_window_starts_with_empty_document(qtbot):
    w = MainWindow()
    qtbot.addWidget(w)
    assert len(w.document.topology.vertices()) == 0
    assert w.current_path is None
    assert "sin titulo" in w.windowTitle()


def test_main_window_new_clears(qtbot):
    w = MainWindow()
    qtbot.addWidget(w)
    t = w.document.topology
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    t.add_edge(v0, v1, Line(v0.point, v1.point))
    assert len(w.document.topology.edges()) == 1

    w._on_new()
    assert len(w.document.topology.edges()) == 0
    assert w.current_path is None


def test_main_window_save_and_reload(qtbot, tmp_path):
    w = MainWindow()
    qtbot.addWidget(w)

    t = w.document.topology
    v0 = t.add_vertex(Point2D(0, 0))
    v1 = t.add_vertex(Point2D(1, 0))
    t.add_edge(v0, v1, Line(v0.point, v1.point))

    path = tmp_path / "proj.json"
    w._save_to(path)
    assert path.exists()
    assert w.current_path == path

    w._on_new()
    assert len(w.document.topology.edges()) == 0

    data = load_project(path)
    loaded = Document.from_dict(data)
    w.document.load_from(loaded)
    assert len(w.document.topology.edges()) == 1
'''


def do_commit_41():
    commit(
        "Commit 41: refactor(gui) main_window usa to_dict/from_dict",
        {
            "src/meshcad/gui/main_window.py": MAIN_WINDOW_PY,
            "tests/gui/test_main_window.py": TEST_MAIN_WINDOW,
        },
        "refactor(gui): main_window usa Document.to_dict/from_dict",
    )


# --------------------------------------------------------------------------- #
# COMMIT 42 - docs
# --------------------------------------------------------------------------- #

DOCS_ARCH_MD = '''# Arquitectura de MeshCAD

## Vision general

    +-----------------+     +-----------------+     +------------------+
    |   core (puro)   |<----|      gui        |<----|      io          |
    |  geometry /     |     |  canvas, tools, |     |  JSON, VTK       |
    |  topology /     |     |  panels, doc    |     |  (puro dict)     |
    |  mesh           |     |  (PyQt5)        |     |                  |
    +-----------------+     +-----------------+     +------------------+
            ^                       ^                        ^
            |                       |                        |
            +---------- no depende de Qt ---------+-----------+

Reglas de dependencia:

- `core` **no** importa PyQt5 ni `gui` ni `io`.
- `gui` puede importar `core` e `io`. Es la unica capa que conoce Qt.
- `io` puede importar `core`. **No** importa `gui`. Trabaja con `dict`.

## Paquetes

- `meshcad.core.geometry`
  - `Point2D`, `Vector2D`
  - `GeometryEntity` (interfaz)
  - `Line`, `Arc`, `Spline`
  - `evaluate(t) -> Point2D` normaliza el parametro a [0, 1].

- `meshcad.core.topology`
  - `Vertex`, `Edge`, `OrientedEdge`: IDs unicos dentro de una `Topology`.
  - `Topology`: contenedor con asignacion monotona de IDs.
  - `Loop`: contorno cerrado. Guarda referencias por id, no copias.
  - `BlockSide`: lado de un bloque (una o varias aristas).
  - `Block`: bloque estructurado de 4 lados.
  - `loop_detector`: deteccion automatica de loops simples.

- `meshcad.core.mesh`
  - `NodeDistribution`, `UniformDistribution`, `BiasedDistribution`.
  - `EdgeMeshSpec`: (edge_id, n_nodes, distribution).
  - `MeshModel`: mapa edge_id -> spec. Una spec por arista.
  - `tfi_grid`: interpolacion transfinita para un cuadrilatero.
  - `mesh_block`: Block + MeshModel + Topology -> BlockMesh.

- `meshcad.gui`
  - `Document`: estado del proyecto + undo stack + to_dict/from_dict.
  - `CadCanvas`: QGraphicsView con preview, snapping, highlights.
  - `tools/`: LineTool, ArcTool, SplineTool, CornerPickerTool.
  - `panels`: LoopsPanel, EdgesPanel, BlocksPanel.

- `meshcad.io`
  - `json_io`: serializacion pura de entidades de `core`.
  - `project_io`: guardar/cargar dict en disco (sin Qt).
  - `vtk_io`: exportacion a PVD + VTS para ParaView.

## Flujo de datos

    CAD (Line/Arc/Spline)
            |
            v
    Topology (Vertex, Edge) ---- Loop (referencias a Edge)
            |                         |
            |                         v
            |                    Block (4 BlockSide)
            |                         |
            v                         v
        MeshModel  ----------->  mesh_block
        (specs por arista)            |
                                      v
                                 BlockMesh (grid)
                                      |
                                      v
                           Canvas / VTK export

## Decisiones de diseno clave

1. **Aristas compartidas por ID**: dos loops que usen la misma arista
   comparten automaticamente su distribucion de nodos. Esto garantiza
   conformidad entre bloques adyacentes sin promediar ni interpolar.

2. **OrientedEdge**: la arista tiene una direccion natural. Si un loop
   la recorre al reves, se marca `reversed=True`. Nunca se duplica.

3. **evaluate(t)**: todas las geometrias exponen un parametro
   normalizado. Las distribuciones producen valores de t, no puntos.

4. **TFI con verificacion de fronteras**: los lados 0/2 y 1/3 se
   muestrean del MeshModel. El interior se calcula por interpolacion
   transfinita. Las fronteras coinciden exactas (verificado por tests).

5. **Document.load_from(other)**: se reemplaza el contenido, no el
   objeto Document, para no romper las conexiones signal/slot.
'''

DOCS_USER_MD = '''# Manual de usuario

## Arranque

    python -m meshcad

## Interfaz

- Barra de herramientas: Seleccionar, Linea, Arco, Spline,
  Generar malla, Borrar malla.
- Menu Archivo: Nuevo, Abrir, Guardar, Guardar como, Exportar malla (VTK).
- Panel izquierdo Loops.
- Paneles derechos Distribuciones y Bloques.

## Flujo tipico

### 1. Dibujar geometria

Pulsa Linea (2 clics), Arco (3 clics: centro, inicio, fin) o
Spline (varios clics + clic derecho para terminar). Mientras mueves
el raton se ve la forma en tiempo real (linea discontinua).

Los vertices existentes se muestran como circulos rojos. Al pasar
cerca con el cursor, la geometria hace snapping.

Escape cancela la herramienta activa.

### 2. Crear un loop

En el panel Loops, pulsa Detectar loops. Se listan los contornos
cerrados. Al seleccionar uno se ilumina en verde sobre el lienzo.

### 3. Crear un bloque

Con un loop seleccionado, pulsa Crear bloque del loop. Haz clic en
4 vertices del loop (en cualquier orden). Se creara un bloque.

### 4. Ajustar distribuciones

En el panel Distribuciones, pulsa Refrescar aristas y edita cada
arista:

- Nodos: numero total incluyendo los extremos.
- Distribucion: uniforme o sesgada con un parametro bias.

Pulsa Aplicar. Si dos bloques comparten una arista, ambos
comparten esta configuracion automaticamente.

### 5. Validar bloques

El panel Bloques muestra si cada bloque tiene los lados opuestos
con el mismo numero de nodos:

- `OK (nodos N x M)`
- `DESAJUSTE lados 0/2: A vs B`

### 6. Generar malla

Pulsa Generar malla. La rejilla aparece sobre los bloques. La barra
de estado indica bloques y celdas.

### 7. Guardar y exportar

- Archivo > Guardar: guarda topologia, distribuciones y bloques en JSON.
- Archivo > Exportar malla (VTK): genera un .pvd y una carpeta
  <nombre>_blocks/ con un .vts por bloque. Abre el .pvd en ParaView.
'''

README_MD = '''# MeshCAD

Mallador 2D estructurado por bloques con un pequeno CAD integrado.

- Version: 1.0.0
- Python: >= 3.9
- GUI: PyQt5

## Instalacion

    pip install -e .

## Uso

    python -m meshcad

Consulta `docs/manual_usuario.md` para el flujo completo.
Consulta `docs/arquitectura.md` para el diseno interno.

## Tests

    python -m pytest

## Estructura

    src/meshcad/
      core/      # geometria, topologia y malla (sin Qt)
        geometry/
        topology/
        mesh/
      gui/       # PyQt5
        tools/
      io/        # JSON y VTK (sin Qt)
    docs/
    tests/

## Reglas de dependencia

- `core` no depende de PyQt5 ni de `gui` ni de `io`.
- `gui` puede importar `core` e `io`.
- `io` puede importar `core` y trabaja con `dict` (sin Qt).

## Roadmap

- [x] Fase 0: estructura del proyecto
- [x] Fase 1: nucleo geometrico 2D
- [x] Fase 2: topologia CAD
- [x] Fase 3: GUI CAD con vista previa en tiempo real
- [x] Fase 4: bloques estructurados de 4 lados
- [x] Fase 5: distribuciones de nodos
- [x] Fase 6: generacion de malla estructurada (TFI)
- [x] Fase 7: persistencia JSON y exportacion VTK
- [x] Fase 8: consolidacion, docs, CI y empaquetado

## Licencia

MIT
'''


def do_commit_42():
    commit(
        "Commit 42: docs",
        {
            "docs/arquitectura.md": DOCS_ARCH_MD,
            "docs/manual_usuario.md": DOCS_USER_MD,
            "README.md": README_MD,
        },
        "docs: manual de usuario y documento de arquitectura",
    )


# --------------------------------------------------------------------------- #
# COMMIT 43 - ruff + mypy
# --------------------------------------------------------------------------- #

PYPROJECT_TOML = '''[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "meshcad"
version = "1.0.0"
description = "Mallador 2D estructurado por bloques con CAD integrado"
readme = "README.md"
requires-python = ">=3.9"
dependencies = [
    "PyQt5",
]

[project.optional-dependencies]
dev = [
    "pytest>=7",
    "pytest-qt",
    "ruff",
    "mypy",
]

[project.scripts]
meshcad = "meshcad.gui.main_window:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "-q"

[tool.ruff]
line-length = 100
target-version = "py39"
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E",
    "F",
    "I",
    "UP",
    "B",
]
ignore = [
    "E501",
    "B008",
]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["E501"]

[tool.mypy]
python_version = "3.9"
ignore_missing_imports = true
warn_unused_ignores = false
exclude = ["build", "dist"]
'''


def do_commit_43():
    commit(
        "Commit 43: ruff y mypy",
        {
            "pyproject.toml": PYPROJECT_TOML,
        },
        "chore: configuracion de ruff y mypy",
    )


# --------------------------------------------------------------------------- #
# COMMIT 44 - CI
# --------------------------------------------------------------------------- #

CI_YML = '''name: ci

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.9", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Instalar dependencias del sistema (Linux)
        if: runner.os == 'Linux'
        run: |
          sudo apt-get update
          sudo apt-get install -y xvfb libgl1 libegl1 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-xinerama0

      - name: Instalar paquete y dependencias
        run: |
          python -m pip install --upgrade pip
          python -m pip install -e .[dev]

      - name: Lint (ruff)
        run: python -m ruff check src tests

      - name: Type check (mypy)
        run: python -m mypy src/meshcad

      - name: Tests (Linux, con xvfb)
        if: runner.os == 'Linux'
        run: xvfb-run -a python -m pytest -q

      - name: Tests (Windows / macOS)
        if: runner.os != 'Linux'
        run: python -m pytest -q
'''


def do_commit_44():
    commit(
        "Commit 44: GitHub Actions",
        {
            ".github/workflows/ci.yml": CI_YML,
        },
        "ci: workflow de GitHub Actions con tests, lint y type-check",
    )


# --------------------------------------------------------------------------- #
# COMMIT 45 - PyInstaller + tag
# --------------------------------------------------------------------------- #

PYINSTALLER_SPEC = '''# -*- mode: python ; coding: utf-8 -*-
"""Especificacion de PyInstaller para MeshCAD.

Construye un ejecutable de un solo directorio en dist/MeshCAD/.
Uso:
    pyinstaller meshcad.spec --noconfirm
"""

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hiddenimports = collect_submodules("meshcad")

a = Analysis(
    ["src/meshcad/__main__.py"],
    pathex=["src"],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MeshCAD",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="MeshCAD",
)
'''

BUILD_SCRIPT = '''"""Construye el ejecutable con PyInstaller.

Uso:
    python build.py

Requiere: pip install pyinstaller
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def main() -> None:
    spec = ROOT / "meshcad.spec"
    if not spec.exists():
        print("ERROR: no existe meshcad.spec")
        sys.exit(1)
    cmd = [sys.executable, "-m", "PyInstaller", str(spec), "--noconfirm"]
    print("  $ " + " ".join(cmd))
    r = subprocess.run(cmd, cwd=str(ROOT))
    if r.returncode != 0:
        sys.exit(r.returncode)
    print()
    print("Ejecutable generado en dist/MeshCAD/")


if __name__ == "__main__":
    main()
'''


def do_commit_45():
    commit(
        "Commit 45: PyInstaller",
        {
            "meshcad.spec": PYINSTALLER_SPEC,
            "build.py": BUILD_SCRIPT,
        },
        "chore: empaquetado con PyInstaller",
    )

    print()
    print("== Creando tag v1.0.0 ==")
    # -f para sobrescribir si ya existe en una ejecucion previa
    run(["git", "tag", "-a", "-f", "v1.0.0", "-m", "MeshCAD 1.0.0"])


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    check()

    do_commit_39()
    do_commit_40()
    do_commit_41()
    do_commit_42()
    do_commit_43()
    do_commit_44()
    do_commit_45()

    print()
    print("== Verificando todos los tests ==")
    run([sys.executable, "-m", "pytest", "-q"])

    print()
    print("== Historial ==")
    run(["git", "log", "--oneline", "--decorate"])

    print()
    print("== Tags ==")
    run(["git", "tag", "-n"])

    print()
    print("Fase 8 completada. Proyecto en v1.0.0.")
    print()
    print("Verifica el desacoplamiento io -> gui con:")
    print('  python -c "import meshcad.io, sys; '
          "assert 'PyQt5' not in sys.modules; "
          "assert 'meshcad.gui' not in sys.modules; "
          "print('io sin Qt: OK')\"")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print()
        print("ERROR:", e)
        sys.exit(1)
    except KeyboardInterrupt:
        print()
        print("Interrumpido por el usuario.")
        sys.exit(130)