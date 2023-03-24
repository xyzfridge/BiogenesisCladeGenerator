from tkinter import filedialog
from pathlib import Path
import traceback

from lib import loader, draw


def main():
    path = filedialog.askdirectory()
    if path == "":
        return
    path = Path(path)

    saves = loader.load_composites(path, verbose=True)
    if not saves:
        print("No world files detected!")
        input()
        return

    clade = draw.CladeDiagram(saves)
    clade.render_to_file(path / "clade.png")


if __name__ == "__main__":
    try:
        main()
    except Exception as exception:
        with open("log.txt", "w") as log_file:
            traceback.print_exception(exception, file=log_file)

        traceback.print_exception(exception)
        input()
