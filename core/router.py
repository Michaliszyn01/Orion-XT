from actions.web import open_any_website, search_website
from actions.apps import open_app, close_app
from actions.files import open_folder
from core.observation import Observation
from registry.resolver import resolve_app, resolve_folder, resolve_website


class Router:
    def __init__(self, memory):
        self.memory = memory

    def _is_success(self, result: str) -> bool:
        lowered = result.lower()

        error_markers = [
            "erro",
            "não consegui",
            "não conheço",
            "não reconhecida",
            "não suportada",
            "não encontrado",
            "não existe",
            "inválido",
        ]

        return not any(marker in lowered for marker in error_markers)

    def execute_single(self, action: dict) -> Observation:
        action_type = action.get("type", "").strip()
        target = action.get("target", "").strip().lower()
        query = action.get("query", "").strip()

        if action_type == "open_website":
            site_key, site_data = resolve_website(target)
            if not site_data:
                return Observation(False, f"Site fora do registry: {target}")

            target = site_key
            result = open_any_website(target)
            self.memory.set_context(last_website=target, last_action="open_website")
            return Observation(self._is_success(result), result)

        if action_type == "search_website":
            if not target:
                target = self.memory.get_context().get("last_website", "")

            site_key, site_data = resolve_website(target)
            if not site_data:
                return Observation(False, f"Site fora do registry: {target}")

            target = site_key

            result = search_website(target, query)
            self.memory.set_context(
                last_website=target,
                last_action="search_website",
                last_query=query
            )
            return Observation(self._is_success(result), result)

        if action_type == "open_app":
            app_key, app_data = resolve_app(target)
            if not app_data:
                return Observation(False, f"Aplicativo fora do registry: {target}")

            target = app_key
            result = open_app(target)
            self.memory.set_context(last_action="open_app")
            return Observation(self._is_success(result), result)

        if action_type == "close_app":
            app_key, app_data = resolve_app(target)
            if not app_data:
                return Observation(False, f"Aplicativo fora do registry: {target}")

            target = app_key
            result = close_app(target)
            self.memory.set_context(last_action="close_app")
            return Observation(self._is_success(result), result)

        if action_type == "open_folder":
            folder_key, folder_data = resolve_folder(target)
            if not folder_data:
                return Observation(False, f"Pasta fora do registry: {target}")

            target = folder_key
            result = open_folder(target)
            self.memory.set_context(last_action="open_folder")
            return Observation(self._is_success(result), result)

        return Observation(False, "Ação não reconhecida.")

    def execute(self, decision: dict) -> Observation:
        if decision.get("type") == "multi_action":
            results = []
            success = True

            for item in decision.get("items", []):
                obs = self.execute_single(item)
                results.append(obs.result)

                if not obs.success:
                    success = False

            return Observation(success, " | ".join(results))

        return self.execute_single(decision)
