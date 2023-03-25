import PyInstaller.__main__
from pathlib import Path
import shutil


VERSION = "0.0.4"


def main():
    PyInstaller.__main__.run([
        "cladegenerator.py",
        "--noconfirm",
        "--specpath", "spec"
    ])

    dist = Path(r"dist")
    cladegenerator = dist / "cladegenerator"

    shutil.copy2("cladegenerator.py", cladegenerator)
    shutil.copy2("README.txt", cladegenerator)
    shutil.copytree("lib", cladegenerator / "lib")

    pack = Path("pack")
    shutil.make_archive(pack / f"cladegenerator-{VERSION}", "zip", dist)


if __name__ == "__main__":
    main()
