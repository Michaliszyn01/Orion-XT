import json
import re

from core.utils import clean_search_query, normalize_target, normalize_text
from registry.resolver import resolve_app, resolve_folder


def pre_classify(user_input: str):
    text = normalize_text(user_input)
    has_search_word = any(x in text for x in ["pesquisa", "procura", "busca"])

    if has_search_word and not any(x in text for x in ["me ensina a", "como pesquisar"]):
        return "force_search"

    if any(x in text for x in [
        "o que e",
        "me explica",
        "me fala sobre",
        "qual a diferenca",
        "como funciona",
        "como eu abro",
        "como abrir",
        "me ensina a",
    ]):
        return {"type": "chat"}

    if has_search_word:
        return "force_search"

    return None


class Agent:
    def __init__(self, client, memory):
        self.client = client
        self.memory = memory

    def _extract_json(self, text: str):
        try:
            return json.loads(text.strip())
        except Exception:
            pass

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                return None

        return None

    def _generate_chat_answer(self, user_input: str) -> str:
        prompt = f"""
Responda em portugues do Brasil, de forma natural e objetiva.
Nao execute acoes no computador.

Mensagem do usuario:
{user_input}
""".strip()

        answer = self.client.generate(prompt).strip()
        return answer or "Entendi."

    def _build_chat_decision(self, user_input: str) -> dict:
        return {
            "type": "chat",
            "thought": "pergunta explicativa; sem acao",
            "answer": self._generate_chat_answer(user_input),
        }

    def _clean_candidate(self, text: str) -> str:
        text = normalize_text(text)
        text = text.split(" e ", 1)[0]
        text = re.sub(r"\b(por favor|pra mim|para mim)\b", " ", text)
        text = re.sub(r"\b(o|a|os|as|um|uma|do|da|dos|das|no|na)\b", " ", text)
        text = re.sub(r"\b(app|aplicativo|programa|site|pasta)\b", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip(" .?!,;:-")

    def _candidate_after_keywords(self, text: str, keywords: list[str]) -> str:
        for keyword in keywords:
            index = text.find(keyword)
            if index >= 0:
                return self._clean_candidate(text[index + len(keyword):])

        return ""

    def _open_decision(self, user_input: str) -> dict | None:
        text = normalize_text(user_input)

        if not any(word in text for word in ["abre", "abra", "abrir", "entra", "acessa"]):
            return None

        target = normalize_target(text)
        if target:
            return {
                "type": "open_website",
                "thought": "site conhecido detectado por regra",
                "target": target,
                "answer": f"Abrindo {target}.",
            }

        candidate = self._candidate_after_keywords(
            text,
            ["abre", "abra", "abrir", "entra", "acessa"],
        )

        app_key, _ = resolve_app(candidate)
        if app_key:
            return {
                "type": "open_app",
                "thought": "aplicativo conhecido detectado por regra",
                "target": app_key,
                "answer": f"Abrindo {app_key}.",
            }

        folder_key, _ = resolve_folder(candidate)
        if folder_key:
            return {
                "type": "open_folder",
                "thought": "pasta conhecida detectada por regra",
                "target": folder_key,
                "answer": f"Abrindo {folder_key}.",
            }

        if candidate:
            return {
                "type": "open_app",
                "thought": "tentativa de abrir aplicativo nao reconhecido",
                "target": candidate,
                "answer": f"Nao conheco o aplicativo {candidate}.",
            }

        return None

    def _close_decision(self, user_input: str) -> dict | None:
        text = normalize_text(user_input)

        if not any(word in text for word in ["fecha", "fechar", "encerra", "encerrar"]):
            return None

        candidate = self._candidate_after_keywords(
            text,
            ["fecha", "fechar", "encerra", "encerrar"],
        )

        app_key, _ = resolve_app(candidate)
        target = app_key or candidate

        if not target:
            return None

        return {
            "type": "close_app",
            "thought": "fechar aplicativo detectado por regra",
            "target": target,
            "answer": f"Fechando {target}.",
        }

    def _usage_decision(self, user_input: str) -> dict | None:
        text = normalize_text(user_input)

        if not any(word in text for word in ["usar", "preciso"]):
            return None

        candidate = self._candidate_after_keywords(text, ["usar", "preciso"])
        app_key, _ = resolve_app(candidate)

        if not app_key:
            return None

        return {
            "type": "open_app",
            "thought": "intencao de usar aplicativo detectada por regra",
            "target": app_key,
            "answer": f"Abrindo {app_key}.",
        }

    def _build_search_decision(self, user_input: str) -> dict:
        text = normalize_text(user_input)
        target = normalize_target(text)
        query = clean_search_query(user_input, target)

        if not target:
            target = self.memory.get_context().get("last_website") or "google"

        if not query:
            query = text

        open_action = self._open_decision(user_input)

        if open_action and " e " in text:
            return {
                "type": "multi_action",
                "thought": "abrir e pesquisar detectado por regra",
                "items": [
                    {
                        "type": open_action["type"],
                        "target": open_action["target"],
                    },
                    {
                        "type": "search_website",
                        "target": target,
                        "query": query,
                    },
                ],
                "answer": f"Abrindo {open_action['target']} e pesquisando {query}.",
            }

        return {
            "type": "search_website",
            "thought": "pesquisa detectada por regra",
            "target": target,
            "query": query,
            "answer": f"Pesquisando {query} em {target}.",
        }

    def _rule_based_decision(self, user_input: str) -> dict | None:
        if " e " in normalize_text(user_input):
            return None

        return (
            self._close_decision(user_input)
            or self._open_decision(user_input)
            or self._usage_decision(user_input)
        )

    def decide(self, user_input: str, observation: dict | None = None) -> dict:
        if observation is None:
            pre = pre_classify(user_input)

            if pre == {"type": "chat"}:
                return self._build_chat_decision(user_input)

            if pre == "force_search":
                return self._build_search_decision(user_input)

            rule_decision = self._rule_based_decision(user_input)
            if rule_decision:
                return rule_decision

        name = self.memory.get_name() or "usuário"
        context = self.memory.get_context()
        history = self.memory.data.get("history", [])[-5:]

        prompt = f"""
Você é o cérebro principal do OrionXT, um assistente desktop em português do Brasil.

Você deve responder SOMENTE com JSON válido.

Tipos permitidos:
- chat
- open_app
- close_app
- open_website
- search_website
- open_folder
- multi_action

Formato chat:
{{
  "type": "chat",
  "thought": "entendi que o usuário quer apenas conversar",
  "answer": "resposta natural"
}}

Formato ação:
{{
  "type": "open_website",
  "thought": "usuário quer abrir o Google",
  "target": "google",
  "answer": "Abrindo o Google."
}}

Formato multi_action:
{{
  "type": "multi_action",
  "thought": "usuário quer abrir o Chrome e pesquisar SQL",
  "items": [
    {{"type": "open_app", "target": "chrome"}},
    {{"type": "search_website", "target": "google", "query": "sql"}}
  ],
  "answer": "Abrindo o Chrome e pesquisando SQL."
}}

Regras:
- Perguntas explicativas devem usar chat.
- Pesquisa, procura ou busca devem usar search_website.
- Em pesquisas, target e query devem ficar separados.
- Use targets limpos como google, youtube, github, wikipedia, alura ou linkedin.
- Não invente ações fora da lista.
- Se for conversa, use chat.
- Se for ação, use o tipo correto.
- Se uma observação anterior mostrar erro, corrija a decisão.
- Não tente mais de uma estratégia complexa.
- Seja objetivo.
- O campo "thought" deve ser curto e técnico.

Usuário atual:
{name}

Contexto:
{json.dumps(context, ensure_ascii=False)}

Histórico:
{json.dumps(history, ensure_ascii=False)}

Observação anterior:
{json.dumps(observation, ensure_ascii=False) if observation else "nenhuma"}

Mensagem do usuário:
{user_input}
""".strip()

        raw = self.client.generate(prompt)
        parsed = self._extract_json(raw)

        if not isinstance(parsed, dict):
            return {
                "type": "chat",
                "thought": "falha ao interpretar resposta do modelo",
                "answer": "Não consegui interpretar isso direito. Pode repetir de outro jeito?"
            }

        return parsed
