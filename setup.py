import PyInstaller.__main__
from pathlib import Path
import shutil


VERSION = "0.1.0"

DIST = Path("dist")
CLADEGENERATOR = DIST / "cladegenerator"

TO_PACK = [
    "cladegenerator.py",
    "README.txt",
    "lib",
    "icon.ico"
]


def main():
    PyInstaller.__main__.run([
        "cladegenerator.py",
        "--noconfirm",
        "--icon=icon.ico"
    ])

    for path in (Path(fp) for fp in TO_PACK):
        if path.is_file():
            shutil.copy2(path, CLADEGENERATOR)
        elif path.is_dir():
            shutil.copytree(path, CLADEGENERATOR / path)
        else:
            print(f"!!!WARNING: Could not copy {path}!!!")

    pack = Path("pack")
    shutil.make_archive(pack / f"cladegenerator-{VERSION}", "zip", DIST)


if __name__ == "__main__":
    main()
