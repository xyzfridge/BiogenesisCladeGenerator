from pathlib import Path
import shutil

CLADE = Path("clade")
CACHE = CLADE / ".cache"
EXPORT = CLADE / "export"

CONFIG = CLADE / "config.ini"


def seek(master: Path, local: Path) -> Path:
    if not master.exists():
        raise ValueError()

    local = master / local

    local.mkdir(parents=True, exist_ok=True)
    return local


def config_status(master: Path) -> tuple[Path, bool]:
    path = master / CONFIG
    created = False

    if not path.exists():
        parent = seek(master, CONFIG.parent)
        shutil.copy2(CONFIG.name, parent)
        created = True

    return path, created


def config(master: Path) -> Path:
    return config_status(master)[0]


def clear(dir_path: Path):
    for path in dir_path.iterdir():
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
