import json
import os


class Memory:
    def __init__(self, path: str = "data/memory.json"):
        self.path = path
        self.data = self._load()

    def _default_data(self):
        return {
            "name": "",
            "preferences": {},
            "history": [],
            "context": {
                "last_website": "",
                "last_action": "",
                "last_query": ""
            }
        }

    def _load(self):
        if not os.path.exists(self.path):
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            default_data = self._default_data()
            self._save(default_data)
            return default_data

        try:
            with open(self.path, "r", encoding="utf-8") as file:
                data = json.load(file)

            if "context" not in data:
                data["context"] = {
                    "last_website": "",
                    "last_action": "",
                    "last_query": ""
                }

            if "history" not in data:
                data["history"] = []

            if "preferences" not in data:
                data["preferences"] = {}

            if "name" not in data:
                data["name"] = ""

            return data
        except Exception:
            return self._default_data()

    def _save(self, data):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def save(self):
        self._save(self.data)

    def add_history(self, user_message: str, assistant_message: str):
        self.data["history"].append({
            "user": user_message,
            "assistant": assistant_message
        })

        self.data["history"] = self.data["history"][-10:]
        self.save()

    def set_name(self, name: str):
        self.data["name"] = name
        self.save()

    def get_name(self):
        return self.data.get("name", "")

    def set_context(self, last_website=None, last_action=None, last_query=None):
        context = self.data.setdefault("context", {})

        if last_website is not None:
            context["last_website"] = last_website

        if last_action is not None:
            context["last_action"] = last_action

        if last_query is not None:
            context["last_query"] = last_query

        self.save()

    def get_context(self):
        return self.data.get("context", {
            "last_website": "",
            "last_action": "",
            "last_query": ""
        })

    def clear_context(self):
        self.data["context"] = {
            "last_website": "",
            "last_action": "",
            "last_query": ""
        }
        self.save()