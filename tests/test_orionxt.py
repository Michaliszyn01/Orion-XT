from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.agent import Agent
from providers.ollama_client import OllamaClient
from registry.resolver import resolve_app, resolve_website


TEST_CASES = [
    # conversa
    {"input": "alô, você está me ouvindo?", "expected_type": "chat"},
    {"input": "me explica o que é programação", "expected_type": "chat"},
    {"input": "me fala sobre python", "expected_type": "chat"},
    {"input": "qual a diferença entre python e javascript?", "expected_type": "chat"},

    # abrir sites
    {"input": "abre o google", "expected_type": "open_website", "expected_target": "google"},
    {"input": "abra o youtube", "expected_type": "open_website", "expected_target": "youtube"},
    {"input": "entra no github", "expected_type": "open_website", "expected_target": "github"},
    {"input": "abre a alura", "expected_type": "open_website", "expected_target": "alura"},
    {"input": "abre o linkedin", "expected_type": "open_website", "expected_target": "linkedin"},

    # pesquisar em sites
    {"input": "pesquisa no google o que é python", "expected_type": "search_website", "expected_target": "google", "expected_query_contains": "python"},
    {"input": "pesquisa no youtube aula de python", "expected_type": "search_website", "expected_target": "youtube", "expected_query_contains": "python"},
    {"input": "procura na alura power bi", "expected_type": "search_website", "expected_target": "alura", "expected_query_contains": "power bi"},
    {"input": "pesquisa no github dashboard power bi", "expected_type": "search_website", "expected_target": "github", "expected_query_contains": "dashboard"},
    {"input": "busca na wikipedia inteligência artificial", "expected_type": "search_website", "expected_target": "wikipedia", "expected_query_contains": "inteligência artificial"},

    # variações com erro de fala/STT
    {"input": "pesquisa na lura python", "expected_type": "search_website", "expected_target": "alura", "expected_query_contains": "python"},
    {"input": "pesquisa no giti rab programação", "expected_type": "search_website", "expected_target": "github", "expected_query_contains": "programação"},
    {"input": "abre o iutube", "expected_type": "open_website", "expected_target": "youtube"},
    {"input": "entra no gugou", "expected_type": "open_website", "expected_target": "google"},

    # abrir apps existentes
    {"input": "abre o bloco de notas", "expected_type": "open_app", "expected_target": "notepad"},
    {"input": "abre a calculadora", "expected_type": "open_app", "expected_target": "calculadora"},
    {"input": "abre o chrome", "expected_type": "open_app", "expected_target": "chrome"},
    {"input": "abre o edge", "expected_type": "open_app", "expected_target": "edge"},
    {"input": "abre o vscode", "expected_type": "open_app", "expected_target": "vscode"},
    {"input": "abre o spotify", "expected_type": "open_app", "expected_target": "spotify"},
    {"input": "abre o excel", "expected_type": "open_app", "expected_target": "excel"},
    {"input": "abre o word", "expected_type": "open_app", "expected_target": "word"},

    # apps inexistentes / não configurados
    {"input": "abre o snap", "expected_error": "unknown_app"},
    {"input": "abre o whatsapp", "expected_error": "unknown_app"},
    {"input": "abre o photoshop", "expected_error": "unknown_app"},
    {"input": "abre o capcut", "expected_error": "unknown_app"},
    {"input": "abre o tiktok", "expected_error": "unknown_app"},

    # fechar apps
    {"input": "fecha o chrome", "expected_type": "close_app", "expected_target": "chrome"},
    {"input": "fecha o spotify", "expected_type": "close_app", "expected_target": "spotify"},
    {"input": "encerra o discord", "expected_type": "close_app", "expected_target": "discord"},
    {"input": "pode fechar o vscode", "expected_type": "close_app", "expected_target": "vscode"},

    # pastas
    {"input": "abre downloads", "expected_type": "open_folder", "expected_target": "downloads"},
    {"input": "abre documentos", "expected_type": "open_folder", "expected_target": "documentos"},
    {"input": "abre área de trabalho", "expected_type": "open_folder", "expected_target": "desktop"},
    {"input": "abre imagens", "expected_type": "open_folder", "expected_target": "imagens"},
    {"input": "abre vídeos", "expected_type": "open_folder", "expected_target": "vídeos"},
    {"input": "abre a pasta do orionxt", "expected_type": "open_folder", "expected_target": "orionxt"},

    # comandos mistos
    {"input": "abre o chrome e pesquisa sql", "expected_type": "multi_action"},
    {"input": "abre o youtube e pesquisa aula de python", "expected_type": "multi_action"},
    {"input": "fecha o spotify e abre o youtube", "expected_type": "multi_action"},
    {"input": "abre o vscode e a pasta do orionxt", "expected_type": "multi_action"},
    {"input": "abre o google e pesquisa engenharia de software", "expected_type": "multi_action"},

    # contexto
    {"input": "agora pesquisa power bi", "expected_type": "search_website", "expected_query_contains": "power bi"},
    {"input": "pesquisa python", "expected_type": "search_website", "expected_query_contains": "python"},
    {"input": "procura aula de excel", "expected_type": "search_website", "expected_query_contains": "excel"},

    # frases ambíguas
    {"input": "alô você consegue abrir o google?", "expected_type": "open_website", "expected_target": "google"},
    {"input": "você pode abrir o youtube pra mim?", "expected_type": "open_website", "expected_target": "youtube"},
    {"input": "queria usar o excel", "expected_type": "open_app", "expected_target": "excel"},
    {"input": "preciso do vscode", "expected_type": "open_app", "expected_target": "vscode"},

    # não deve executar ação
    {"input": "como eu abro o google manualmente?", "expected_type": "chat"},
    {"input": "me ensina a pesquisar no youtube", "expected_type": "chat"},
    {"input": "o que é github?", "expected_type": "chat"},
    {"input": "o que é alura?", "expected_type": "chat"},
]

ERROR_TYPES = {
    "wrong_intent",
    "wrong_target",
    "hallucinated_action",
    "execution_mismatch",
    "validation_failed",
    "unknown_app",
}

ALLOWED_ACTIONS = {
    "chat",
    "open_app",
    "close_app",
    "open_website",
    "search_website",
    "open_folder",
    "multi_action",
}


@dataclass
class Observation:
    success: bool
    message: str
    error_type: str | None = None


@dataclass
class TestResult:
    user_input: str
    expected_type: str
    received_type: str
    success: bool
    error_type: str
    message: str
    decision: dict[str, Any]
    expected_target: str = ""
    received_target: str = ""
    observation: Observation | None = None


class TestMemory:
    """Memoria em RAM para nao alterar data/memory.json durante os testes."""

    def __init__(self):
        self.data = {
            "name": "",
            "preferences": {},
            "history": [],
            "context": {
                "last_website": "",
                "last_action": "",
                "last_query": "",
            },
        }

    def get_name(self):
        return self.data.get("name", "")

    def get_context(self):
        return self.data.get("context", {})


class Validator:
    def validate(self, decision: Any) -> Observation:
        if not isinstance(decision, dict):
            return Observation(False, "Decisao nao retornou um objeto JSON.", "validation_failed")

        return self._validate_action(decision)

    def _validate_action(self, action: dict[str, Any]) -> Observation:
        action_type = self._text(action.get("type"))

        if not action_type:
            return Observation(False, "Campo 'type' ausente.", "validation_failed")

        if action_type not in ALLOWED_ACTIONS:
            return Observation(False, f"Acao inventada: {action_type}", "hallucinated_action")

        if action_type == "chat":
            answer = self._text(action.get("answer"))
            if not answer:
                return Observation(False, "Chat sem campo 'answer'.", "validation_failed")
            return Observation(True, "OK")

        if action_type == "multi_action":
            return self._validate_multi_action(action)

        target_required = {"open_app", "close_app", "open_website", "search_website", "open_folder"}
        if action_type in target_required and not self._text(action.get("target")):
            return Observation(False, f"Acao '{action_type}' sem campo 'target'.", "validation_failed")

        if action_type == "search_website" and not self._text(action.get("query")):
            return Observation(False, "Pesquisa sem campo 'query'.", "validation_failed")

        return Observation(True, "OK")

    def _validate_multi_action(self, action: dict[str, Any]) -> Observation:
        items = action.get("items")

        if not isinstance(items, list) or not items:
            return Observation(False, "multi_action sem lista 'items'.", "validation_failed")

        for index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                return Observation(False, f"Item {index} nao e um objeto JSON.", "validation_failed")

            result = self._validate_action(item)
            if not result.success:
                return Observation(False, f"Item {index}: {result.message}", result.error_type)

        return Observation(True, "OK")

    @staticmethod
    def _text(value: Any) -> str:
        return str(value or "").strip()


class FakeRouter:
    def execute(self, decision):
        action_type = decision.get("type")

        if action_type == "multi_action":
            results = []

            for item in decision.get("items", []):
                result = self.execute(item)
                results.append(result)

                if not result.success:
                    return Observation(
                        False,
                        " | ".join(item.message for item in results),
                        result.error_type,
                    )

            return Observation(True, " | ".join(item.message for item in results) or "OK")

        if action_type == "open_website":
            return Observation(True, f"Abrindo {decision.get('target')}")

        if action_type == "search_website":
            return Observation(
                True,
                f"Pesquisando {decision.get('query')} em {decision.get('target')}",
            )

        if action_type == "open_app":
            app_key, app_data = resolve_app(decision.get("target"))
            if not app_data:
                return Observation(False, "Aplicativo desconhecido", "unknown_app")
            return Observation(True, f"Abrindo {app_key}")

        return Observation(True, "OK")


def normalize(value: Any) -> str:
    return str(value or "").strip().lower()


def canonical_target(action_type: str, target: str) -> str:
    target = normalize(target)

    if action_type in {"open_website", "search_website"}:
        key, _ = resolve_website(target)
        return key or target

    if action_type in {"open_app", "close_app"}:
        key, _ = resolve_app(target)
        return key or target

    return target


def answer_conflicts_with_observation(decision: dict[str, Any], observation: Observation) -> bool:
    answer = normalize(decision.get("answer"))
    if not answer:
        return False

    failure_words = ["erro", "falha", "nao consegui", "não consegui", "desconhecido", "invalido", "inválido"]
    success_words = ["abrindo", "pesquisando", "fechando", "ok", "feito"]

    says_failure = any(word in answer for word in failure_words)
    says_success = any(word in answer for word in success_words)

    if observation.success:
        return says_failure

    return says_success and not says_failure


def analyze_result(
    test_case: dict[str, Any],
    decision: dict[str, Any],
    validation: Observation,
    observation: Observation | None,
) -> TestResult:
    user_input = test_case["input"]
    expected_type = test_case.get("expected_type", "")
    expected_error = test_case.get("expected_error", "")
    expected_target = test_case.get("expected_target", "")
    received_type = normalize(decision.get("type"))
    received_target = normalize(decision.get("target"))

    if not validation.success:
        error_type = validation.error_type or "validation_failed"
        return TestResult(
            user_input,
            expected_type or expected_error,
            received_type,
            False,
            error_type,
            validation.message,
            decision,
            expected_target,
            received_target,
            observation,
        )

    if expected_error:
        if expected_error == "unknown_app" and received_type != "open_app":
            return TestResult(
                user_input,
                expected_error,
                received_type,
                False,
                "wrong_intent",
                "Esperava uma tentativa de abrir aplicativo desconhecido.",
                decision,
                expected_target,
                received_target,
                observation,
            )

        if observation and observation.error_type == expected_error:
            return TestResult(
                user_input,
                expected_error,
                received_type,
                True,
                expected_error,
                observation.message,
                decision,
                expected_target,
                received_target,
                observation,
            )

        return TestResult(
            user_input,
            expected_error,
            received_type,
            False,
            "execution_mismatch",
            f"Esperava erro '{expected_error}', mas ele nao aconteceu.",
            decision,
            expected_target,
            received_target,
            observation,
        )

    if expected_type and received_type != expected_type:
        return TestResult(
            user_input,
            expected_type,
            received_type,
            False,
            "wrong_intent",
            "Tipo de decisao diferente do esperado.",
            decision,
            expected_target,
            received_target,
            observation,
        )

    if expected_target:
        expected_canonical = canonical_target(received_type, expected_target)
        received_canonical = canonical_target(received_type, received_target)

        if expected_canonical != received_canonical:
            return TestResult(
                user_input,
                expected_type,
                received_type,
                False,
                "wrong_target",
                "Target diferente do esperado.",
                decision,
                expected_target,
                received_target,
                observation,
            )

    if observation and not observation.success:
        return TestResult(
            user_input,
            expected_type,
            received_type,
            False,
            "execution_mismatch",
            observation.message,
            decision,
            expected_target,
            received_target,
            observation,
        )

    if observation and answer_conflicts_with_observation(decision, observation):
        return TestResult(
            user_input,
            expected_type,
            received_type,
            False,
            "execution_mismatch",
            "Resposta da IA nao bate com a observacao do roteador.",
            decision,
            expected_target,
            received_target,
            observation,
        )

    return TestResult(
        user_input,
        expected_type,
        received_type,
        True,
        "success",
        observation.message if observation else "OK",
        decision,
        expected_target,
        received_target,
        observation,
    )


def run_test_case(agent: Agent, validator: Validator, router: FakeRouter, test_case: dict[str, Any]) -> TestResult:
    decision = agent.decide(test_case["input"])
    validation = validator.validate(decision)
    observation = router.execute(decision) if validation.success else None
    return analyze_result(test_case, decision, validation, observation)


def print_test_result(result: TestResult) -> None:
    status = "✅ SUCESSO" if result.success else "❌ ERRO"

    print(f"[TESTE] {result.user_input}")
    print(f"Tipo esperado: {result.expected_type or '-'}")
    print(f"Tipo recebido: {result.received_type or '-'}")

    if result.expected_target:
        print(f"Target esperado: {result.expected_target}")
        print(f"Target recebido: {result.received_target or '-'}")

    if result.observation:
        print(f"Observacao: {result.observation.message}")

    print(f"STATUS: {status}")
    print(f"MOTIVO: {result.error_type}")

    if not result.success:
        print(f"DETALHE: {result.message}")

    print("-----------------------------------")


def print_summary(results: list[TestResult]) -> None:
    total = len(results)
    success_count = sum(1 for result in results if result.success)
    error_count = total - success_count
    accuracy = int((success_count / total) * 100) if total else 0

    print("RESUMO:")
    print(f"Total: {total}")
    print(f"Sucesso: {success_count}")
    print(f"Erro: {error_count}")
    print(f"Taxa de acerto: {accuracy}%")


def build_agent() -> Agent:
    model = os.getenv("ORIONXT_TEST_MODEL", "gemma3:4b")
    base_url = os.getenv("ORIONXT_OLLAMA_URL", "http://localhost:11434")
    client = OllamaClient(model=model, base_url=base_url)
    return Agent(client, TestMemory())


def run_all_tests() -> list[TestResult]:
    agent = build_agent()
    validator = Validator()
    router = FakeRouter()
    results = []

    for test_case in TEST_CASES:
        result = run_test_case(agent, validator, router, test_case)
        results.append(result)
        print_test_result(result)

    print_summary(results)
    return results


if __name__ == "__main__":
    final_results = run_all_tests()
    all_passed = all(result.success for result in final_results)
    raise SystemExit(0 if all_passed else 1)
