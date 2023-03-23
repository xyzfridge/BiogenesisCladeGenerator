import PyInstaller.__main__
from pathlib import Path
import shutil


VERSION = "0.0.2"
name = f"cladegenerator-{VERSION}"


def main():
    PyInstaller.__main__.run([
        "cladegenerator.py",
        "--noconfirm",
        "--specpath", "spec"
    ])

    dist = Path(r"dist/cladegenerator")

    shutil.copy2("cladegenerator.py", dist)
    shutil.copytree("lib", dist / "lib")

    shutil.make_archive(dist.parent / name, "zip", dist)


if __name__ == "__main__":
    main()
