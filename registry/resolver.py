import os
from pathlib import Path
from difflib import get_close_matches

from registry.apps import APPS
from registry.websites import WEBSITES
from registry.folders import FOLDERS


def normalize(text: str) -> str:
    return text.lower().strip()


def expand_path(path: str) -> Path | str:
    if path == "ms-settings:":
        return path

    expanded = os.path.expandvars(path.replace("/", os.sep))
    return Path(expanded)


def find_by_alias(registry: dict, name: str):
    name = normalize(name)

    if name in registry:
        return name, registry[name]

    alias_map = {}

    for key, data in registry.items():
        alias_map[normalize(key)] = key

        for alias in data.get("aliases", []):
            alias_map[normalize(alias)] = key

    if name in alias_map:
        key = alias_map[name]
        return key, registry[key]

    # fuzzy matching leve
    matches = get_close_matches(
        name,
        alias_map.keys(),
        n=1,
        cutoff=0.82
    )

    if matches:
        key = alias_map[matches[0]]
        return key, registry[key]

    return None, None


def resolve_app(name: str):
    return find_by_alias(APPS, name)


def resolve_website(name: str):
    return find_by_alias(WEBSITES, name)


def resolve_folder(name: str):
    return find_by_alias(FOLDERS, name)


def first_existing_path(paths: list[str]):
    for raw_path in paths:
        path = expand_path(raw_path)

        if isinstance(path, str):
            return path

        if path.exists():
            return path

    if paths:
        return expand_path(paths[0])

    return None


def known_website_names():
    names = set()

    for key, data in WEBSITES.items():
        names.add(normalize(key))
        for alias in data.get("aliases", []):
            names.add(normalize(alias))

    return names