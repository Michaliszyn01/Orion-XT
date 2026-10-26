import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from voice.tts import speak

speak("Teste de voz do Orion. Se você está ouvindo isso, funcionou.")