# Demonstração isolada — contexto e memória

Executada em 28/10/2026, Python 3.12.14. A demonstração instancia `Database`, `MemoryStore` e `ContextEngine` com SQLite temporário. Não inicia `main.py`, voz, navegador, automação de aplicativos ou Ollama. Os dados são exemplos fictícios.

```json
[
  {
    "input": "hoje vamos estudar função do segundo grau",
    "output": "Entendido. Seu foco de estudo agora é função do segundo grau."
  },
  {
    "input": "minha dificuldade é interpretar gráfico",
    "output": "Registrei essa dificuldade no seu contexto de estudo atual."
  },
  {
    "input": "o que eu estou estudando?",
    "output": "Seu foco atual de estudo é função do segundo grau."
  }
]
```

É uma verificação do componente de memória/contexto. Não comprova funcionamento completo de voz, roteamento por modelo ou ações do assistente. Os pontos de entrada usados podem ser encontrados em `storage/database.py`, `storage/memory_store.py` e `core/context_engine.py`.
