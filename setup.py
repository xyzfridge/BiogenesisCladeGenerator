import PyInstaller.__main__
from pathlib import Path
import shutil


VERSION = "0.0.1"
name = f"cladegenerator-{VERSION}"


def main():
    PyInstaller.__main__.run([
        "cladegenerator.py",
        "--noconfirm",
        "--name", name,
        "--specpath", "spec"
    ])

    dist = Path("dist") / name

    shutil.copy2("cladegenerator.py", dist)
    shutil.copytree("lib", dist / "lib")

    shutil.make_archive(dist, "zip", dist)


if __name__ == "__main__":
    main()
