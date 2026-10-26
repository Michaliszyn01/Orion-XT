from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from storage.memory_store import MemoryStore


if __name__ == "__main__":
    store = MemoryStore()

    store.save_event("test", "Evento de teste do OrionXT", importance=1)
    store.save_short_memory("test", "Memoria curta de teste", importance=1)
    store.save_long_memory("test", "test_key", "Valor de teste", importance=1)

    print(store.get_recent_events())
    print(store.get_relevant_memories())
