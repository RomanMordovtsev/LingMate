import os
from pathlib import Path
from typing import Dict, Literal, List

# Настройки путей
BASE_DIR = Path(__file__).parent.parent
DB_DIR = BASE_DIR / "data"
DB_DIR.mkdir(exist_ok=True)

# Пути к файлам данных
CHAT_HISTORY_PATH = DB_DIR / "chat_history.json"
USER_SETTINGS_PATH = DB_DIR / "user_settings.json"

# Голосовые параметры (для совместимости, не используется в XTTS)
VOICE_CONFIG: Dict[str, Dict[str, str]] = {
    "male": {},
    "female": {}
}

# Настройки форматирования ответов
RESPONSE_FORMAT = {
    "section_headers": {
        "target": "### 1. Основной ответ ({language})",
        "translation": "### 2. Дословный перевод ({native_lang})",
        "analysis": "### 3. Разбор фраз",
        "advanced": "### 4. Дополнительно"
    },
    "markers": {
        "keywords": "➤",
        "mistakes": "⚠️",
        "culture": "🌍",
        "nuances": "💡",
        "alternatives": "🔍"
    }
}

MENTOR_PROMPT_TEMPLATE = """
Ты — AI-преподаватель языков. Всегда строго следуй формату:

### 1. Основной ответ ({target_language})
[Ответ только на целевом языке. Без переводов!]

### 2. Дословный перевод ({native_language})
[Переведи текст из раздела 1 на {native_language}. Только перевод, без пояснений!]

### 3. Разбор фраз
- ➤ **Ключевые слова**:
  [Слово/фраза 1] - [значение на {native_language}] (пример: "[пример] → [перевод]")
- ⚠️ **Типичные ошибки**:
  [Неправильно] → [Правильно] (объяснение: "[на {native_language}]")
- 🌍 **Культурный контекст**:
  [Факт или норма на {native_language}]

### 4. Дополнительно
- 💡 **Нюансы**:
  [Объяснение на {native_language}]
- 🔍 **Альтернативы**:
  [Варианты на {target_language} с пояснениями на {native_language}]

---
### Жесткие правила:
1. Все пояснения только на {native_language}.
2. Для примеров используй кавычки: «пример».
3. Учитывай уровень пользователя ({level}).
"""

# Настройки генеративного AI
GEMINI_CONFIG = {
    "model_name": "gemini-1.5-pro-latest",
    "safety_settings": [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
    ],
    "generation_config": {
        "temperature": 0.7,
        "top_p": 0.9,
        "max_output_tokens": 2000,
        "stop_sequences": ["###"]
    }
}

# Уровни сложности
LEVEL_DESCRIPTIONS = {
    "A1": "Начинающий (понимает простые фразы)",
    "A2": "Элементарный (может общаться на бытовые темы)",
    "B1": "Средний (может поддерживать беседу)",
    "B2": "Выше среднего (свободно говорит на большинство тем)",
    "C1": "Продвинутый (понимает сложные тексты)",
    "C2": "Владение в совершенстве"
}

# Настройки для автонапоминаний
REMINDER_SETTINGS = {
    "min_interval_hours": 24,
    "max_interval_hours": 48,
    "reminder_messages": {
        "en": [
            "Hey! Let's practice some {language} today!",
            "Ready for our daily {language} chat?"
        ],
        "ru": [
            "Привет! Давай сегодня попрактикуем {language}!",
            "Готов к нашей ежедневной практике {language}?"
        ]
    }
}

# Настройки TTS
TTS_CONFIG = {
    "model": "xtts_v2",
    "languages": {},  # Используется только для валидации при необходимости
    "default_speaker": "female",
    "silence_duration_ms": 800
}

# Максимальная длина текста для TTS (в символах)
TTS_MAX_LENGTH = {
    'af': 200, 'al': 200, 'am': 200, 'arb': 200, 'arm': 200, 'az': 200,
    'bela': 200, 'ben': 200, 'bir': 200, 'bos': 200, 'bul': 200,
    'cam': 200, 'can': 200, 'cat': 200, 'cro': 200, 'cze': 200,
    'dan': 200, 'dar': 200, 'deu': 200, 'dut': 200,
    'en': 250,
    'est': 200, 'es': 239,
    'far': 200, 'fin': 200, 'fr': 230,
    'gal': 200, 'geo': 200, 'gr': 200, 'gud': 200,
    'heb': 200, 'hin': 200, 'hun': 200, 'icl': 200,
    'ind': 200, 'it': 230, 'ja': 150, 'kaz': 200, 'khm': 200,
    'ko': 200, 'lao': 200, 'lat': 200, 'lit': 200,
    'mac': 200, 'mala': 200, 'malt': 200, 'man': 200,
    'mon': 200, 'nep': 200, 'nor': 200, 'phil': 200,
    'pol': 200, 'por': 230, 'pu': 200,
    'ro': 200, 'ru': 182, 'sco': 200, 'se': 200,
    'sin': 200, 'slova': 200, 'slove': 200, 'som': 200,
    'sun': 200, 'swa': 200, 'swe': 200,
    'tai': 200, 'tam': 200, 'thai': 200,
    'tur': 200, 'uk': 200, 'ur': 200, 'uz': 200,
    'val': 200, 'vas': 200, 'vie': 200
}

# Лимиты для безопасности
SAFETY_LIMITS = {
    "max_text_length": 1000,
    "min_interval_seconds": 5
}

# Настройки кэширования
CACHE_SETTINGS = {
    "voice_cache_ttl": 3600,
    "max_cache_size": 100
}

DEFAULT_SETTINGS = {
    "max_response_length": 500,
    "auto_reminders": True,
    "speech_speed": 1.0,
    "feedback_level": "detailed"
}

# Настройки референсных голосов
VOICE_REFERENCE_FORMATS = {
    "en": "{lang}_{region}_{gender}.wav",
    "es": "{lang}_{region}_{gender}.wav",
    # Остальные используют формат без региона
}

DEFAULT_REGIONS = {
    "en": "us",
    "es": "eu"
}

STREAMING_CONFIG = {
    "max_queue_size": 20,
    "preload_seconds": 0.5
}

VOICE_SETTINGS = {
    "max_retries": 3,
    "retry_delay": 0.5,
    "cleanup_interval": 3600,
    "max_temp_files": 100,
    "fallback_voices": {
        "en": {"gender": "female", "region": "us"},
        "ru": {"gender": "female", "region": None}
    }
}

DEFAULT_VOICE_SETTINGS = {
    "gender": "female",
    "native_lang": "ru"
}

NATIVE_LANG_LABELS = {
    "ru": "русский",
    "lit": "литовский",
    "en": "английский",
    "es": "испанский",
    "fr": "французский",
    "de": "немецкий",
    "ja": "японский",
    # ... и т.д.
}

# Добавляем в конец файла:
TTS_SUPPORTED_LANGUAGES = [
    'en', 'es', 'fr', 'de', 'it', 'pt', 'pl', 'tr', 'ru',
    'nl', 'cs', 'ar', 'zh-ccn', 'hu', 'ko', 'ja', 'hi'
]

FALLBACK_LANGUAGE = 'ru'  # Язык для fallback
