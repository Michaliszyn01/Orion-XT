from registry.resolver import resolve_app, resolve_folder, resolve_website


ALLOWED_TYPES = {
    "chat",
    "open_app",
    "close_app",
    "open_website",
    "search_website",
    "open_folder",
    "multi_action",
}


class Validator:
    def validate(self, decision: dict) -> tuple[bool, str]:
        if not isinstance(decision, dict):
            return False, "A decisao nao e um JSON valido."

        action_type = decision.get("type")

        if action_type not in ALLOWED_TYPES:
            return False, f"Tipo de acao invalido: {action_type}"

        if action_type == "chat":
            if not decision.get("answer"):
                return False, "Resposta de chat vazia."
            return True, ""

        if action_type == "multi_action":
            items = decision.get("items")

            if not isinstance(items, list) or not items:
                return False, "multi_action sem lista de acoes."

            for item in items:
                valid, error = self.validate(item)
                if not valid:
                    return False, error

            return True, ""

        if action_type in ["open_app", "close_app", "open_website", "open_folder"]:
            if not decision.get("target"):
                return False, f"Acao {action_type} sem target."

            target = decision.get("target")

            if action_type in ["open_app", "close_app"]:
                _, app_data = resolve_app(target)
                if not app_data:
                    return False, f"Aplicativo fora do registry: {target}"

            if action_type == "open_website":
                _, site_data = resolve_website(target)
                if not site_data:
                    return False, f"Site fora do registry: {target}"

            if action_type == "open_folder":
                _, folder_data = resolve_folder(target)
                if not folder_data:
                    return False, f"Pasta fora do registry: {target}"

            return True, ""

        if action_type == "search_website":
            if not decision.get("query"):
                return False, "Pesquisa sem query."

            if not decision.get("target"):
                return False, "Pesquisa sem target."

            target = decision.get("target")
            _, site_data = resolve_website(target)
            if not site_data:
                return False, f"Site fora do registry: {target}"

            return True, ""

        return False, "Acao desconhecida."
