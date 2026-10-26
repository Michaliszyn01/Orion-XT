from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from storage.database import Database
from storage.memory_store import MemoryStore
from core.context_engine import ContextEngine


if __name__ == "__main__":
    db = Database("data/test_context_persistence.sqlite3")
    store = MemoryStore(db)

    engine = ContextEngine(store)
    print(engine.handle("hoje vamos estudar função do segundo grau"))
    print(engine.handle("minha dificuldade é interpretar gráfico"))

    engine2 = ContextEngine(store)

    print(engine2.handle("o que eu estou estudando?"))
    print(engine2.handle("qual o próximo passo?"))
