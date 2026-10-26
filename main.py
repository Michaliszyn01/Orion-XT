import time

from providers.ollama_client import OllamaClient
from core.memory import Memory
from core.agent import Agent
from core.context_engine import ContextEngine
from core.router import Router
from core.assistant import Assistant
from core.modes import ModeManager
from storage.memory_store import MemoryStore
from voice.normalizer import normalize_voice_text
from voice.stt import SpeechToText
from voice.tts import is_speaking, speak


def main():
    memory = Memory()
    client = OllamaClient(model="gemma3:4b")

    agent = Agent(client, memory)
    router = Router(memory)
    mode_manager = ModeManager()
    memory_store = MemoryStore()
    context_engine = ContextEngine(memory_store)
    assistant = Assistant(agent, router, memory, mode_manager, memory_store, context_engine)

    stt = SpeechToText(model_size="base")

    print("OrionXT iniciado.")
    print("Digite uma mensagem ou aperte Enter vazio para falar.")
    print("Digite 'sair' para encerrar.")

    while True:
        typed_input = input("Você: ").strip()

        if typed_input.lower() in ["sair", "exit", "quit"]:
            print("OrionXT: Até mais.")
            break

        if typed_input:
            user_input = typed_input
        else:
            while is_speaking():
                time.sleep(0.05)

            user_input = stt.listen(
                max_duration=15,
                silence_threshold=0.015,
                silence_duration=0.35,
                min_recording_duration=0.25
            )

            if user_input:
                original_input = user_input
                user_input = normalize_voice_text(user_input)

                if original_input != user_input:
                    print(f"Você disse: {original_input}")
                    print(f"Corrigido para: {user_input}")
                else:
                    print(f"Você disse: {user_input}")
            elif stt.last_error:
                print(f"OrionXT: {stt.last_error}")
                continue

        if not user_input:
            print("OrionXT: Não consegui entender.")
            continue

        response = assistant.handle(user_input)
        print(f"OrionXT: {response}")
        speak(response)


if __name__ == "__main__":
    main()
