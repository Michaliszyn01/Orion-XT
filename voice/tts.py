import asyncio
import ctypes
import os
import queue
import re
import tempfile
import threading

try:
    import edge_tts
except ImportError:
    edge_tts = None


VOICE = "pt-BR-AntonioNeural"
MAX_SPEECH_CHARS = 400

_speech_queue = queue.Queue()
_speaking = False
_worker_started = False


def clean_text(text: str) -> str:
    text = text.replace("**", "")
    text = text.replace("*", "")
    text = text.replace("\n", ". ")
    return text.strip()


def split_text_for_tts(text: str, max_chars: int = 450) -> list[str]:
    text = clean_text(text)

    if not text:
        return []

    if len(text) <= max_chars:
        return [text]

    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?;])\s+", text)
        if sentence.strip()
    ]

    chunks = []
    current = ""

    for sentence in sentences:
        if len(sentence) > max_chars:
            if current:
                chunks.append(current)
                current = ""

            chunks.extend(_split_long_sentence(sentence, max_chars))
            continue

        candidate = f"{current} {sentence}".strip()

        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = sentence

    if current:
        chunks.append(current)

    return chunks


def _split_long_sentence(sentence: str, max_chars: int) -> list[str]:
    words = sentence.split()
    chunks = []
    current = ""

    for word in words:
        if len(word) > max_chars:
            if current:
                chunks.append(current)
                current = ""

            chunks.extend(
                word[index:index + max_chars]
                for index in range(0, len(word), max_chars)
            )
            continue

        candidate = f"{current} {word}".strip()

        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = word

    if current:
        chunks.append(current)

    return chunks


def _mci(command: str):
    error = ctypes.windll.winmm.mciSendStringW(command, None, 0, None)

    if error:
        buffer = ctypes.create_unicode_buffer(255)
        ctypes.windll.winmm.mciGetErrorStringW(error, buffer, 255)
        raise RuntimeError(f"MCI erro {error}: {buffer.value}")


def _play_mp3(filename: str):
    alias = "orion_tts"

    _mci(f'open "{filename}" type mpegvideo alias {alias}')
    try:
        _mci(f"play {alias} wait")
    finally:
        _mci(f"close {alias}")


async def _speak(text: str):
    text = clean_text(text)

    if not text:
        return

    if edge_tts is None:
        print("Erro no TTS: edge-tts nao esta instalado.")
        return

    filename = ""

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as file:
            filename = file.name

        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(filename)

        _play_mp3(filename)
    finally:
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except OSError as e:
                print("Erro ao remover audio temporario do TTS:", repr(e))


def is_speaking() -> bool:
    return _speaking or not _speech_queue.empty()


def _speech_worker():
    global _speaking

    while True:
        text = _speech_queue.get()

        if text is None:
            _speech_queue.task_done()
            break

        try:
            _speaking = True
            asyncio.run(_speak(text))
        except Exception as e:
            print("Erro no TTS:", repr(e))
        finally:
            _speaking = False
            _speech_queue.task_done()


def _ensure_worker():
    global _worker_started

    if _worker_started:
        return

    thread = threading.Thread(target=_speech_worker, daemon=True)
    thread.start()
    _worker_started = True


def speak(text: str):
    text = clean_text(text)

    if not text:
        return

    _ensure_worker()

    for chunk in split_text_for_tts(text, MAX_SPEECH_CHARS):
        _speech_queue.put(chunk)


def speak_blocking(text: str):
    text = clean_text(text)

    if not text:
        return

    for chunk in split_text_for_tts(text, MAX_SPEECH_CHARS):
        try:
            asyncio.run(_speak(chunk))
        except Exception as e:
            print("Erro no TTS:", repr(e))
