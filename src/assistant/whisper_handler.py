import speech_recognition as sr
import numpy as np
import torch
import concurrent.futures
import time
import threading


class WhisperHandler:
    """
    Lightweight, safer Whisper wrapper with lazy model loading,
    proper 16k conversion from speech_recognition AudioData,
    optional async transcription and reduced memory footprint.
    """
    
    def __init__(self, model_name="base", device=None, max_workers=2):
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._model = None
        self._whisper_module = None
        self.recognizer = sr.Recognizer()
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self._load_lock = threading.Lock()
        self._whisper_available = None  # None => not checked, False => unavailable, True => available

    def _load_model(self):
        # thread-safe lazy import + load
        if self._model is not None:
            return

        with self._load_lock:
            if self._model is not None:
                return

            # Lazy import whisper to avoid import-time crashes on unsupported platforms
            if self._whisper_available is None:
                try:
                    import whisper as _whisper  # local import
                    self._whisper_module = _whisper
                    self._whisper_available = True
                except Exception as e:
                    self._whisper_available = False
                    print(f"Whisper import failed (will disable Whisper): {e}")
                    return

            if not self._whisper_available:
                return

            try:
                print(f"Loading Whisper model '{self.model_name}' on {self.device}...")
                # use the whisper module loaded above
                self._model = self._whisper_module.load_model(self.model_name, device=self.device)
                print("✅ Whisper model loaded")
            except Exception as e:
                print(f"Failed to load Whisper model: {e}")
                self._model = None
                self._whisper_available = False

    @property
    def model(self):
        if self._model is None:
            self._load_model()
        return self._model

    def transcribe_audio(self, audio_data: sr.AudioData, language="en", fp16=None):
        """
        Synchronous transcription. Forces conversion to 16k and int16 -> float32.
        If Whisper is unavailable returns empty string so caller can fallback.
        """
        # If whisper import or load failed, return empty so HybridRecognizer can fallback
        if self._whisper_available is False:
            return ""

        try:
            raw = audio_data.get_raw_data(convert_rate=16000, convert_width=2)
            audio_np = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

            self._load_model()
            if self._model is None:
                return ""

            fp16 = (self.device == "cuda") if fp16 is None else fp16
            with torch.no_grad():
                # whisper expects either a numpy array or file path
                result = self._model.transcribe(audio_np, language=language, fp16=fp16, task="transcribe")
            return (result.get("text") or "").strip()
        except Exception as e:
            print(f"Whisper transcription error: {e}")
            return ""

    def transcribe_file(self, audio_file_path, language="en"):
        if self._whisper_available is False:
            return ""
        try:
            self._load_model()
            if self._model is None:
                return ""
            fp16 = (self.device == "cuda")
            with torch.no_grad():
                result = self._model.transcribe(audio_file_path, language=language, fp16=fp16)
            return (result.get("text") or "").strip()
        except Exception as e:
            print(f"File transcription error: {e}")
            return ""

    def transcribe_async(self, audio_data: sr.AudioData, language="en"):
        """
        Return a Future for non-blocking transcription.
        """
        return self._executor.submit(self.transcribe_audio, audio_data, language)

    def get_model_info(self):
        return {
            "device": self.device,
            "model_type": type(self._model).__name__ if self._model else None,
            "is_multilingual": getattr(self._model, "is_multilingual", None),
            "whisper_available": self._whisper_available
        }


class HybridRecognizer:
    """
    Hybrid recognizer that can use both Whisper and Google Speech API.
    Falls back to Google if Whisper fails.
    """
    
    def __init__(self, use_whisper=True, whisper_model="base"):
        self.use_whisper = use_whisper
        self.recognizer = sr.Recognizer()

        if use_whisper:
            try:
                # constructor of WhisperHandler no longer imports whisper at module import
                self.whisper = WhisperHandler(model_name=whisper_model)
                print("✅ Hybrid mode: Whisper (primary) + Google (fallback)")
            except Exception as e:
                print(f"⚠️ Whisper initialization failed: {e}")
                print("Falling back to Google Speech API only")
                self.use_whisper = False
                self.whisper = None
        else:
            self.whisper = None
            print("✅ Using Google Speech API only")

    def recognize(self, audio_data, language="en", timeout=None):
        """
        Try Whisper first (sync). If it's still empty, fallback to Google.
        """
        if self.use_whisper and self.whisper:
            try:
                text = self.whisper.transcribe_audio(audio_data, language=language)
                if text:
                    return text
            except Exception:
                # ensure fallback on any whisper failure
                pass

        # Fallback to Google (speech_recognition)
        try:
            return self.recognizer.recognize_google(audio_data, language=language).lower()
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            print(f"Google API error: {e}")
            return ""
