from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from storage.database import Database
from storage.memory_store import MemoryStore
from core.context_engine import ContextEngine


if __name__ == "__main__":
    db = Database("data/test_academic_context.sqlite3")
    store = MemoryStore(db)
    engine = ContextEngine(store)

    tests = [
        "tirei 700 no enem",
        "quero chegar em 740 no enem",
        "minha nota em matemática foi 650",
        "tirei 880 na redação",
        "quero fazer engenharia de software na ufpr",
        "qual minha estratégia para o enem?",
    ]

    for text in tests:
        print("USER:", text)
        print("ORION:", engine.handle(text))
        print("-" * 40)

    engine2 = ContextEngine(store)
    print("PERSISTENCIA:")
    print("ORION:", engine2.handle("como eu chego na minha meta?"))
