"""Construye el ejecutable con PyInstaller.

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
