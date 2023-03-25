import json

import javaobj.v2 as javaobj
from collections import UserDict
from typing import Any
from pathlib import Path

from .datamodel import World
from .composite import WorldComposite


class _IdentityDict(UserDict):
    def __setitem__(self, key, value):
        super().__setitem__(id(key), value)

    def __getitem__(self, item):
        return super().__getitem__(id(item))

    def __delitem__(self, key):
        super().__delitem__(id(key))

    def copy(self):
        new_dict = _IdentityDict()
        new_dict.data = self.data.copy()
        return new_dict


def load_bgw(path, verbose=False):
    if verbose:
        print(f"Reading {path}...")

    with open(path, "rb") as bgw_file:
        return javaobj.load(bgw_file)


def _strip_key_underscores(d: dict, recursive=False):
    keys = list(d.keys())
    for k, v in list(d.items()):
        if (k_stripped := k.lstrip("_")) not in keys:
            del d[k]
            d[k_stripped] = v

        if recursive:
            if isinstance(v, dict):
                _strip_key_underscores(v, True)
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        _strip_key_underscores(item, True)


def javaobj_to_data(jobj: Any, _stack=None):
    _stack = _IdentityDict() if _stack is None else _stack

    if existing_obj := _stack.get(jobj) is not None:
        return existing_obj

    def recur(obj, cont):
        next_stack = _stack.copy()
        next_stack[jobj] = cont
        return javaobj_to_data(obj, _stack=next_stack)

    match jobj:
        case javaobj.beans.JavaString():
            return jobj.value

        case javaobj.transformers.JavaList() | javaobj.beans.JavaArray():
            container = []
            for o in jobj:
                container.append(recur(o, container))
            return container

        case javaobj.beans.JavaInstance():
            classdict = jobj.field_data[jobj.classdesc]
            field_names = [f.name for f in classdict.keys()]
            field_values = list(classdict.values())
            container = dict(zip(field_names, field_values))

            _strip_key_underscores(container)

            for k, v in list(container.items()):
                container[k] = recur(v, container)

            return container

        case _:
            return jobj


def load_bgw_data(path, verbose=False):
    path = Path(path)
    filename = path.name

    bgw = load_bgw(path, verbose)

    if verbose:
        print(f"Indexing {filename}...")

    data = javaobj_to_data(bgw)

    if verbose:
        print(f"Finished indexing {filename}.")

    return data


def load_bgw_as_world(path, verbose=False):
    return World(load_bgw_data(path, verbose))


def load_json_data(path, verbose=False):
    path = Path(path)

    with path.open('r') as json_file:
        data = json.load(json_file)

    _strip_key_underscores(data, recursive=True)
    data["organisms"] = {"list": data["organisms"]}

    if verbose:
        print(f"Read {path.name}.")

    return data


def load_json_as_world(path, verbose=False):
    return World(load_json_data(path, verbose))


def _get_clade_dir(path):
    path = Path(path)

    clade_dir = path / ".clade"
    if not clade_dir.exists():
        clade_dir.mkdir()

    return clade_dir


def _get_clade_cache_dir(path):
    clade_dir = _get_clade_dir(path)

    cache_dir = clade_dir / "cache"
    if not cache_dir.exists():
        cache_dir.mkdir()

    return cache_dir


def load_composite_from_save(path, verbose=False) -> WorldComposite:
    path = Path(path)

    cache = _get_clade_cache_dir(path.parent)

    if (cached_composite := cache / f"{path.stem}.json").exists():
        return load_composite_from_cache(cached_composite, verbose)
    else:
        match path.suffix:
            case '.json':
                world = load_json_as_world(path, verbose=verbose)
            case '.bgw':
                world = load_bgw_as_world(path, verbose=verbose)
            case _:
                raise ValueError()

        composite = WorldComposite(world)

        with cached_composite.open('w') as file:
            json.dump(composite.to_data_dict(), file)

        if verbose:
            print(f"Saved {path.name} data to cache.")

        return composite


def load_composite_from_cache(path, verbose=False):
    path = Path(path)

    with path.open('r') as file:
        data = json.load(file)
    composite = WorldComposite(data)

    if verbose:
        print(f"Loaded {path.stem} from cache.")

    return composite


def _to_names(fps: list[Path]):
    return [fp.stem for fp in fps]


def load_composites(path, verbose=False) -> list[WorldComposite]:
    path = Path(path)

    composites = []
    loaded_names = []

    def not_loaded(fp):
        return fp.stem not in loaded_names

    cached_jsons = list(_get_clade_cache_dir(path).glob('*.json'))
    composites += [load_composite_from_cache(fp, verbose=verbose) for fp in cached_jsons
                   if not_loaded(fp)]
    loaded_names += _to_names(cached_jsons)

    json_saves = list(path.glob('*@*.json'))
    composites += [load_composite_from_save(fp, verbose=verbose) for fp in json_saves
                   if not_loaded(fp)]
    loaded_names += _to_names(json_saves)

    bgw_saves = list(path.glob('*@*.bgw'))
    composites += [load_composite_from_save(fp, verbose=verbose) for fp in bgw_saves
                   if not_loaded(fp)]
    # loaded_names += _to_names(bgw_saves)

    composites.sort(key=lambda c: c.time)

    if verbose:
        print(f"Loaded {len(composites)} world checkpoints.")

    return composites
