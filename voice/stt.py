import os
import tempfile
import time

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from scipy.io.wavfile import write


VIRTUAL_DEVICE_KEYWORDS = (
    "voicemod",
    "mapeador",
    "mapper",
    "dummy",
    "line out",
    "wave speaker",
    "stereo mix",
)


class SpeechToText:
    def __init__(self, model_size="base", language="pt", device=None):
        self.language = language
        self.device = device
        self.last_error = ""
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def _is_virtual_device(self, device_name: str) -> bool:
        normalized_name = device_name.lower()
        return any(keyword in normalized_name for keyword in VIRTUAL_DEVICE_KEYWORDS)

    def _pick_input_device(self):
        if self.device is not None:
            return self.device

        devices = [
            device
            for device in sd.query_devices()
            if device.get("max_input_channels", 0) > 0
        ]

        if not devices:
            raise RuntimeError("Nenhum microfone disponivel.")

        default_input = None
        default_config = sd.default.device

        if isinstance(default_config, (list, tuple)) and default_config:
            default_input = default_config[0]
        elif isinstance(default_config, int):
            default_input = default_config

        default_device = next(
            (device for device in devices if device.get("index") == default_input),
            None,
        )

        if default_device and not self._is_virtual_device(default_device["name"]):
            return default_device

        preferred_device = next(
            (device for device in devices if not self._is_virtual_device(device["name"])),
            None,
        )

        if preferred_device:
            return preferred_device

        if default_device:
            return default_device

        return devices[0]

    def _resolve_samplerate(self, device, requested_samplerate):
        if requested_samplerate is not None:
            try:
                sd.check_input_settings(
                    device=device,
                    samplerate=requested_samplerate,
                    channels=1,
                    dtype="int16",
                )
                return int(requested_samplerate)
            except Exception:
                pass

        try:
            device_info = sd.query_devices(device)
            fallback_samplerate = int(device_info["default_samplerate"])
            sd.check_input_settings(
                device=device,
                samplerate=fallback_samplerate,
                channels=1,
                dtype="int16",
            )
            return fallback_samplerate
        except Exception as exc:
            raise RuntimeError(
                f"Nao consegui configurar o microfone selecionado: {exc}"
            ) from exc

    def listen(
        self,
        samplerate=None,
        silence_threshold=0.025,
        silence_duration=0.8,
        max_duration=15,
        min_recording_duration=0.6,
        duration=None,
    ):
        if duration is not None:
            max_duration = duration

        self.last_error = ""

        try:
            selected_device = self._pick_input_device()
            device_id = (
                selected_device["index"]
                if isinstance(selected_device, dict)
                else selected_device
            )
            device_name = (
                selected_device["name"]
                if isinstance(selected_device, dict)
                else sd.query_devices(selected_device)["name"]
            )
            samplerate = self._resolve_samplerate(device_id, samplerate)
        except Exception as exc:
            self.last_error = f"Falha ao iniciar o microfone: {exc}"
            return ""

        print(f"Estou te ouvindo pelo microfone: {device_name}")

        audio_buffer = []
        speech_started = False
        speech_start = None
        silence_start = None
        capture_start = time.time()

        def callback(indata, frames, callback_time, status):
            nonlocal speech_started, speech_start, silence_start

            if status and not self.last_error:
                self.last_error = f"Captura de audio com aviso: {status}"

            audio_buffer.append(indata.copy())

            normalized_audio = indata.astype(np.float32) / np.iinfo(np.int16).max
            volume = float(np.sqrt(np.mean(normalized_audio ** 2)))

            if volume > silence_threshold:
                speech_started = True
                speech_start = speech_start or time.time()
                silence_start = None
                return

            if speech_started and silence_start is None:
                silence_start = time.time()

        try:
            with sd.InputStream(
                samplerate=samplerate,
                device=device_id,
                channels=1,
                dtype="int16",
                callback=callback,
            ):
                while True:
                    elapsed = time.time() - capture_start

                    if elapsed >= max_duration:
                        break

                    if not speech_started:
                        time.sleep(0.05)
                        continue

                    speech_elapsed = time.time() - speech_start
                    if speech_elapsed < min_recording_duration:
                        time.sleep(0.05)
                        continue

                    if silence_start and (time.time() - silence_start) >= silence_duration:
                        break

                    time.sleep(0.05)
        except Exception as exc:
            self.last_error = f"Falha ao capturar audio: {exc}"
            return ""

        if not speech_started or not audio_buffer:
            return ""

        audio = np.concatenate(audio_buffer, axis=0)
        audio_path = None

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as file:
                audio_path = file.name

            write(audio_path, samplerate, audio)

            segments, _ = self.model.transcribe(
                audio_path,
                language=self.language,
                vad_filter=True,
            )

            return " ".join(segment.text.strip() for segment in segments).strip()
        except Exception as exc:
            self.last_error = f"Falha ao transcrever audio: {exc}"
            return ""
        finally:
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)
