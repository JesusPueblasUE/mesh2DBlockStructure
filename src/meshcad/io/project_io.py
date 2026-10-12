"""Guardar y cargar proyectos en formato JSON."""

from __future__ import annotations

import json
from pathlib import Path

from meshcad.gui.document import Document


def save_project(document: Document, path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = document.to_dict()
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_project(path) -> Document:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return Document.from_dict(data)
