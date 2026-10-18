"""Build the executable with PyInstaller.

Usage:
    python build.py

Requires: pip install pyinstaller
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def main() -> None:
    spec = ROOT / "meshcad.spec"
    if not spec.exists():
        print("ERROR: meshcad.spec does not exist")
        sys.exit(1)
    cmd = [sys.executable, "-m", "PyInstaller", str(spec), "--noconfirm"]
    print("  $ " + " ".join(cmd))
    r = subprocess.run(cmd, cwd=str(ROOT))
    if r.returncode != 0:
        sys.exit(r.returncode)
    print()
    print("Executable generated in dist/MeshCAD/")


if __name__ == "__main__":
    main()
