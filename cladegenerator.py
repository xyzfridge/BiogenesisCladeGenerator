import tkinter
from tkinter import filedialog
from pathlib import Path
import traceback

from lib import loader, draw, config, paths
from lib.paths import seek


def main():
    tk = tkinter.Tk()
    tk.withdraw()
    tk.iconbitmap("icon.ico")

    path = filedialog.askdirectory()
    if path == "":
        return
    path = Path(path)

    saves = loader.load_composites(path, verbose=True)
    if not saves:
        print("No world files detected!")
        input()
        return

    start, end = (i if i != -1 else len(saves) for i in (config.clade_start, config.clade_end))
    saves = saves[start-1:end]

    def generate_clade(gstart=0, glast=len(saves), gi=None):
        if glast >= 0:
            glast = min(glast, len(saves))
        clade = draw.CladeDiagram(saves[gstart:glast])
        number = f"-{gi + 1}" if gi is not None else ""
        clade.render_to_file(seek(path, paths.EXPORT) / f"clade{number}.{config.file_type}")

    interval = config.clade_split_interval
    if interval != -1:
        start = 0
        last = len(saves)
        for i, end in enumerate(range(start+interval, last+interval, interval)):
            generate_clade(start, end, i)
            start = end
    else:
        generate_clade()


if __name__ == "__main__":
    try:
        main()
    except Exception as exception:
        with open("log.txt", "w") as log_file:
            traceback.print_exception(exception, file=log_file)

        traceback.print_exception(exception)
        input()
