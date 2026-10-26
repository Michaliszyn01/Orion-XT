import webbrowser

from core.agent import Agent
from core.router import Router
from core.memory import Memory
from core.modes import ModeManager, ORION_SPOTIFY_URL
from core.utils import normalize_text
from core.validator import Validator


def is_orion_mode_command(text: str) -> bool:
    text = normalize_text(text)

    aliases = [
        "modo orion",
        "mado orion",
        "moto orion",
        "modo audio",
        "modo oreo",
        "moutro oreo",
        "outro oreo",
        "orion",
    ]

    return any(alias in text for alias in aliases)


def is_activate_orion_command(text: str) -> bool:
    text = normalize_text(text)

    activation_words = [
        "ativa",
        "ativar",
        "inicia",
        "iniciar",
        "liga",
        "ligar",
    ]

    standalone_commands = [
        "modo orion",
        "mado orion",
        "moto orion",
        "modo audio",
        "modo oreo",
        "moutro oreo",
        "outro oreo",
    ]

    words = set(text.split())

    return is_orion_mode_command(text) and (
        any(word in words for word in activation_words)
        or text in standalone_commands
    )


def is_deactivate_orion_command(text: str) -> bool:
    text = normalize_text(text)

    return (
        "modo normal" in text
        or "sair do modo orion" in text
        or "desativar modo orion" in text
        or "desativa modo orion" in text
    )


class Assistant:
    def __init__(
        self,
        agent: Agent,
        router: Router,
        memory: Memory,
        mode_manager: ModeManager | None = None,
        memory_store=None,
        context_engine=None,
    ):
        self.agent = agent
        self.router = router
        self.memory = memory
        self.validator = Validator()
        self.mode_manager = mode_manager if mode_manager is not None else ModeManager()
        self.memory_store = memory_store
        self.context_engine = context_engine

    def _save_interaction_event(self, user_input: str, answer: str):
        if self.memory_store is None:
            return

        try:
            self.memory_store.save_event(
                event_type="interaction",
                content=f"USER: {user_input}\nORION: {answer}",
                importance=1,
                metadata={
                    "user_input": user_input,
                    "assistant_response": answer,
                },
            )
        except Exception as exc:
            print("Erro ao salvar evento no banco:", repr(exc))

    def _record_interaction(self, user_input: str, answer: str):
        self.memory.add_history(user_input, answer)
        self._save_interaction_event(user_input, answer)

    def _open_orion_theme(self):
        try:
            webbrowser.open(ORION_SPOTIFY_URL)
        except Exception as exc:
            print("Erro ao abrir musica do Modo Orion:", repr(exc))

    def _handle_mode_command(self, user_input: str) -> str | None:
        if is_activate_orion_command(user_input):
            self.mode_manager.activate_orion_mode()
            self._open_orion_theme()
            return "Modo Orion ativado. Estou online e pronto para operar."

        if is_deactivate_orion_command(user_input):
            self.mode_manager.deactivate_orion_mode()
            return "Modo Orion desativado. Voltando ao modo normal."

        return None

    def handle(self, user_input: str) -> str:
        lowered = user_input.lower().strip()

        if lowered.startswith("meu nome é "):
            name = user_input[11:].strip()
            self.memory.set_name(name)
            answer = f"Entendido. Vou te chamar de {name}."
            self._save_interaction_event(user_input, answer)
            return answer

        mode_answer = self._handle_mode_command(user_input)
        if mode_answer is not None:
            self._record_interaction(user_input, mode_answer)
            return mode_answer

        if self.context_engine is not None:
            try:
                context_response = self.context_engine.handle(user_input)
            except Exception as exc:
                print("Erro no Context Engine:", repr(exc))
                context_response = None

            if context_response:
                self._record_interaction(user_input, context_response)
                return context_response

        decision = self.agent.decide(user_input)

        valid, error = self.validator.validate(decision)

        if not valid:
            observation = {
                "success": False,
                "result": error
            }

            decision = self.agent.decide(user_input, observation=observation)
            valid, error = self.validator.validate(decision)

            if not valid:
                answer = "Não consegui transformar isso em uma ação segura."
                self._record_interaction(user_input, answer)
                return answer

        if decision.get("type") == "chat":
            answer = decision.get("answer", "Entendi.")
            self._record_interaction(user_input, answer)
            return answer

        observation = self.router.execute(decision)

        if not observation.success:
            corrected_decision = self.agent.decide(
                user_input,
                observation=observation.to_dict()
            )

            valid, error = self.validator.validate(corrected_decision)

            if valid and corrected_decision.get("type") != "chat":
                second_observation = self.router.execute(corrected_decision)

                answer = corrected_decision.get("answer") or second_observation.result
                self._record_interaction(user_input, answer)
                return answer

            answer = corrected_decision.get("answer", observation.result)
            self._record_interaction(user_input, answer)
            return answer

        answer = decision.get("answer") or observation.result
        self._record_interaction(user_input, answer)
        return answer
