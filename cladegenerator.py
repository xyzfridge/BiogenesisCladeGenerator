from tkinter import filedialog
from pathlib import Path

from lib import loader, draw


def main():
    path = Path(filedialog.askdirectory())
    saves = loader.load_composites(path, verbose=True)
    clade = draw.CladeDiagram(saves)
    clade.render_to_file(path / "clade.png")


if __name__ == "__main__":
    main()
