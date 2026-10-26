from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from storage.memory_store import MemoryStore
from core.context_engine import ContextEngine


if __name__ == "__main__":
    store = MemoryStore()
    engine = ContextEngine(store)

    tests = [
        "hoje vamos estudar função do segundo grau",
        "minha dificuldade é interpretar gráfico",
        "você não vai me explicar ou?",
        "aprendi hoje sobre vértice da parábola",
        "o que eu estou estudando?",
        "qual o próximo passo?",
        "terminei de estudar",
    ]

    for text in tests:
        print("USER:", text)
        print("ORION:", engine.handle(text))
        print("-" * 40)
