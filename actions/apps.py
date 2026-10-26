import os
import subprocess
from pathlib import Path

from registry.resolver import resolve_app, first_existing_path

def _silent_popen(command):
    return subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        shell=False,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

def open_app(app_name: str) -> str:
    app_key, app_data = resolve_app(app_name)

    if not app_data:
        return f"Não conheço o aplicativo '{app_name}'."

    paths = app_data.get("paths", [])
    target = first_existing_path(paths)

    if not target:
        return f"O aplicativo '{app_name}' não tem caminho configurado."

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

    if not process_names:
        return f"O aplicativo '{app_key}' não tem processo configurado para fechar."

    found_any = False
    closed_any = False

    for process_name in process_names:
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