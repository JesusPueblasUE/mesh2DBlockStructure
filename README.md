# MeshCAD

A 2D block-structured mesh generator with an integrated CAD editor.

- Version: 1.0.0
- Python: 3.9 or newer
- GUI: PyQt5

## Installation

    pip install -e .

## Usage

    python -m meshcad

See `docs/user_manual.md` for the workflow and `docs/architecture.md` for the internal design.

## Tests

    python -m pytest

## Dependency rules

- `core` does not depend on PyQt5, `gui`, or `io`.
- `gui` may import `core` and `io`.
- `io` may import `core` and works with plain dictionaries.

## License

MIT
