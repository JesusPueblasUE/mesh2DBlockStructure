"""Guardar y cargar proyectos en formato JSON (puro dict).

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
