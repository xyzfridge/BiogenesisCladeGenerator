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

    config_path, config_created = paths.config_status(path)
    if config_created:
        print(f"Created config.ini in {path.name}/clade. You may edit it now. (Be sure to save any changes.)")
        print("Press enter to continue when ready...")
        input()
    config.update(config_path)

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

    paths.clear(seek(path, paths.EXPORT))

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
    except MemoryError:
        print(f"Ran out of memory! The clade diagram is likely too large to be rendered. Try setting "
              f"clade_split_interval{' to a lower value' if config.clade_split_interval != -1 else ''} in the config.")
        input()
    except Exception as exception:
        with open("log.txt", "w") as log_file:
            traceback.print_exception(exception, file=log_file)

        traceback.print_exception(exception)
        input()
