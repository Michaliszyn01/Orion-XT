import os
from pathlib import Path

from registry.resolver import resolve_folder, first_existing_path


def open_folder(target: str) -> str:
    folder_key, folder_data = resolve_folder(target)

    if not folder_data:
        return f"Pasta '{target}' não reconhecida."

    paths = folder_data.get("paths", [])
    folder_path = first_existing_path(paths)

    if not folder_path:
        return f"Nenhum caminho configurado para a pasta '{folder_key}' foi encontrado neste PC."

    if isinstance(folder_path, Path) and not folder_path.exists():
        return f"A pasta '{folder_path}' não existe."

    try:
        os.startfile(str(folder_path))
        return f"Abrindo pasta {folder_key}."
    except Exception as e:
        return f"Erro ao abrir pasta {folder_key}: {e}"
