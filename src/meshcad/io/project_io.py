"""Save and load projects in JSON format (plain dictionaries).

Este modulo NO depende de la GUI: recibe y devuelve diccionarios.
La conversion dict <-> Document vive en la capa de GUI, que es la
single que conoce Qt. Asi `meshcad.io` se can importar without tener
PyQt5 instalado.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def save_project(data: Dict[str, Any], path) -> None:
    """Write a serialized project to disk as JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_project(path) -> Dict[str, Any]:
    """Read a project from disk and return its dictionary."""
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8"))
