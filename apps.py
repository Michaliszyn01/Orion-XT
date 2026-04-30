import os
import re
import subprocess
from pathlib import Path

from registry.resolver import resolve_app, first_existing_path


PROCESS_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,126}\.exe$", re.IGNORECASE)


def _silent_popen(command):
    return subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        shell=False,
        creationflags=subprocess.CREATE_NO_WINDOW
    )


def _clean_process_name(process_name: str) -> str | None:
    if not isinstance(process_name, str):
        return None

    value = process_name.strip()

    if not value:
        return None

    if any(separator in value for separator in ("/", "\\", ":")):
        return None

    if any(char.isspace() for char in value):
        return None

    if not PROCESS_NAME_PATTERN.fullmatch(value):
        return None

    return value


def _validated_process_names(process_names) -> list[str] | None:
    if not isinstance(process_names, list):
        return None

    validated = []

    for process_name in process_names:
        cleaned = _clean_process_name(process_name)

        if not cleaned:
            return None

        validated.append(cleaned)

    return validated


def open_app(app_name: str) -> str:
    app_key, app_data = resolve_app(app_name)

    if not app_data:
        return f"Não conheço o aplicativo '{app_name}'."

    paths = app_data.get("paths", [])

    if not paths:
        return f"O aplicativo '{app_key}' não tem caminho configurado."

    target = first_existing_path(paths)

    if not target:
        return f"Nenhum caminho configurado para '{app_key}' foi encontrado neste PC."

    try:
        launch_args = app_data.get("launch_args", [])

        if isinstance(target, Path):
            if not target.exists():
                return f"O aplicativo '{app_key}' não foi encontrado nesse PC."

            if launch_args:
                _silent_popen([str(target), *launch_args])
            else:
                _silent_popen([str(target)])
            return f"Abrindo {app_key}."

        if isinstance(target, str) and target == "ms-settings:":
            os.startfile(target)
            return "Abrindo configurações."

        if isinstance(target, str):
            _silent_popen([target])
            return f"Abrindo {app_key}."

        return f"Não consegui abrir '{app_key}'."
    except Exception as e:
        return f"Erro ao abrir {app_key}: {e}"


def close_app(app_name: str) -> str:
    app_key, app_data = resolve_app(app_name)

    if not app_data:
        return f"Não conheço o aplicativo '{app_name}' para fechar."

    process_names = app_data.get("process_names", [])

    validated_process_names = _validated_process_names(process_names)

    if validated_process_names is None:
        return f"Configuração insegura de processo para '{app_key}'."

    if not validated_process_names:
        return f"O aplicativo '{app_key}' não tem processo configurado para fechar."

    found_any = False
    closed_any = False

    for process_name in validated_process_names:
        try:
            check = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {process_name}"],
                capture_output=True,
                text=True,
                shell=False,
            )

            output = (check.stdout or "") + (check.stderr or "")

            if process_name.lower() in output.lower():
                found_any = True

                kill = subprocess.run(
                    ["taskkill", "/IM", process_name, "/F"],
                    capture_output=True,
                    text=True,
                    shell=False,
                )

                if kill.returncode == 0:
                    closed_any = True
        except Exception:
            continue

    if closed_any:
        return f"Fechando {app_key}."

    if not found_any:
        return f"O aplicativo '{app_key}' não está aberto."

    return f"Não consegui fechar '{app_key}'."
