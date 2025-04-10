import os
import tempfile
from pathlib import Path
from typing import Optional, List
import logging
from datetime import datetime
from queue import Queue
from threading import Thread, Lock
import time
from TTS.api import TTS
import sounddevice as sd
import soundfile as sf
import re
from .config import (
    VOICE_REFERENCE_FORMATS,
    DEFAULT_REGIONS,
    TTS_MAX_LENGTH,
    VOICE_SETTINGS,
    TTS_SUPPORTED_LANGUAGES,
    FALLBACK_LANGUAGE
)

logger = logging.getLogger(__name__)


class VoiceHandler:
    def __init__(self):
        self.temp_dir = self._setup_temp_dir()
        self.reference_dir = Path("reference_speakers_wav")
        self.reference_dir.mkdir(exist_ok=True)
        self.audio_queue = Queue()
        self.active_files = set()
        self.lock = Lock()
        self.playback_thread = Thread(target=self._playback_worker, daemon=True)
        self.playback_thread.start()
        self.cleanup_thread = Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()

        try:
            self.tts = TTS(
                model_name="tts_models/multilingual/multi-dataset/xtts_v2",
                progress_bar=False,
                gpu=False
            )
            logger.info("XTTS v2 model initialized")
        except Exception as e:
            logger.critical(f"TTS init failed: {e}")
            raise

    def _setup_temp_dir(self) -> Path:
        temp_dir = Path("D:/pythonProject1/audio_temp")
        try:
            temp_dir.mkdir(exist_ok=True, mode=0o777)
            test_file = temp_dir / "test_permission.txt"
            test_file.write_text("test")
            test_file.unlink()
            return temp_dir
        except Exception as e:
            logger.error(f"Could not setup temp dir: {e}")
            return Path(tempfile.gettempdir())

    # Модифицируем метод speak_response:
    def speak_response(self, text: str, target_lang: str, **kwargs) -> bool:
        """Генерация и воспроизведение с полной предварительной подготовкой"""
        try:
            native_lang = kwargs.get('native_lang', 'ru')

            # Проверяем и корректируем языки при необходимости
            target_lang = target_lang if target_lang in TTS_SUPPORTED_LANGUAGES else FALLBACK_LANGUAGE
            native_lang = native_lang if native_lang in TTS_SUPPORTED_LANGUAGES else FALLBACK_LANGUAGE

            # Генерация всех аудиофрагментов
            target_files = self._generate_audio(
                self._extract_section(text, "Основной ответ"),
                target_lang,
                gender=kwargs.get('gender', 'female'),
                region=kwargs.get('region')
            ) if text else []

            native_files = self._generate_audio(
                self._extract_section(text, "Дословный перевод"),
                native_lang,
                gender=kwargs.get('gender', 'female'),
                region=kwargs.get('region')
            ) if text else []

            # Воспроизведение по очереди
            for file in target_files + native_files:
                self.audio_queue.put(file)

            return True
        except Exception as e:
            logger.error(f"Speech synthesis failed: {e}")
            return False

    def _generate_audio(self, text: str, lang: str, **kwargs) -> List[Path]:
        if not text:
            return []

        ref_path = self._get_reference_path(lang, kwargs['gender'], kwargs.get('region'))
        fragments = self._split_text(text, lang)
        audio_files = []

        for i, fragment in enumerate(fragments):
            temp_path = self.temp_dir / f"temp_{os.getpid()}_{int(time.time())}_{i}.wav"

            for attempt in range(VOICE_SETTINGS['max_retries']):
                try:
                    self.tts.tts_to_file(
                        text=fragment,
                        speaker_wav=str(ref_path),
                        language=lang,
                        file_path=str(temp_path),
                        split_sentences=True
                    )
                    with self.lock:
                        self.active_files.add(temp_path)
                    audio_files.append(temp_path)
                    break
                except Exception as e:
                    if attempt == VOICE_SETTINGS['max_retries'] - 1:
                        logger.error(f"Failed after {VOICE_SETTINGS['max_retries']} attempts: {e}")
                        raise
                    time.sleep(VOICE_SETTINGS['retry_delay'])
                    continue

        return audio_files

    def _playback_worker(self):
        while True:
            audio_file = self.audio_queue.get()
            try:
                if not audio_file.exists():
                    logger.warning(f"Audio file missing: {audio_file}")
                    continue

                audio_data, samplerate = sf.read(audio_file)
                sd.play(audio_data, samplerate)
                sd.wait()
            except Exception as e:
                logger.error(f"Playback failed: {e}")
            finally:
                self._safe_delete(audio_file)

    def _cleanup_worker(self):
        while True:
            time.sleep(VOICE_SETTINGS['cleanup_interval'])
            self._cleanup_temp_files()

    def _cleanup_temp_files(self):
        with self.lock:
            current_files = list(self.active_files)
            deleted = 0

            for file in current_files:
                if not file.exists():
                    self.active_files.remove(file)
                    deleted += 1

            logger.info(f"Cleanup: Removed {deleted} stale files")

    def _safe_delete(self, file_path: Path):
        with self.lock:
            if file_path in self.active_files:
                try:
                    if file_path.exists():
                        file_path.unlink()
                    self.active_files.remove(file_path)
                except Exception as e:
                    logger.warning(f"Could not delete {file_path}: {e}")

    def _split_text(self, text: str, lang: str) -> List[str]:
        max_len = TTS_MAX_LENGTH.get(lang, 350)

        if lang in ["ja", "zh"]:
            sentences = re.split(r'(?<=[。！？…])', text)
        else:
            sentences = re.split(r'(?<=[.!?…]) +', text)

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(current_chunk) + len(sentence) <= max_len:
                current_chunk += " " + sentence if current_chunk else sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk)

        valid_chunks = []
        for chunk in chunks:
            if len(chunk) > max_len * 1.1:
                words = chunk.split()
                temp_chunk = ""
                for word in words:
                    if len(temp_chunk) + len(word) + 1 <= max_len:
                        temp_chunk += " " + word if temp_chunk else word
                    else:
                        if temp_chunk:
                            valid_chunks.append(temp_chunk)
                        temp_chunk = word
                if temp_chunk:
                    valid_chunks.append(temp_chunk)
            else:
                valid_chunks.append(chunk)

        return valid_chunks

    # Модифицируем метод _get_reference_path:
    def _get_reference_path(self, lang: str, gender: str, region: Optional[str] = None) -> Path:
        try:
            # Проверяем поддержку языка
            if lang not in TTS_SUPPORTED_LANGUAGES:
                logger.warning(f"Language {lang} not supported, falling back to {FALLBACK_LANGUAGE}")
                lang = FALLBACK_LANGUAGE

            fmt = VOICE_REFERENCE_FORMATS.get(lang, "{lang}_{gender}.wav")
            region = region or DEFAULT_REGIONS.get(lang)
            filename = fmt.format(lang=lang, gender=gender, region=region)
            path = self.reference_dir / filename

            if not path.exists():
                fallback = VOICE_SETTINGS['fallback_voices'].get(lang)
                if fallback:
                    filename = fmt.format(
                        lang=lang,
                        gender=fallback['gender'],
                        region=fallback.get('region')
                    )
                    path = self.reference_dir / filename

            return path
        except Exception as e:
            logger.error(f"Error getting reference path: {e}")
            raise

    def _extract_section(self, text: str, section_title: str) -> Optional[str]:
        if not isinstance(text, str) or not text.strip():
            return None

        try:
            pattern = rf"### \d+\. {re.escape(section_title)}.*?\n(.*?)(?=###|\Z)"
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            return match.group(1).strip() if match else None
        except Exception as e:
            logger.error(f"Text extraction error: {e}")
            return None