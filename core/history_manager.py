import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
from .config import CHAT_HISTORY_PATH, USER_SETTINGS_PATH
from .models import UserSettings
# Замените все print на logger:
import logging
logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        self._init_files()

    def _init_files(self):
        """Инициализация файлов базы данных"""
        for path in [CHAT_HISTORY_PATH, USER_SETTINGS_PATH]:
            try:
                if not path.exists():
                    path.parent.mkdir(exist_ok=True)
                    path.write_text("{}", encoding="utf-8")
            except Exception as e:
                logger.error(f"Error initializing DB file {path}: {e}")
                raise

    def save_message(self, user_id: str, message: str, sender: str = "user") -> None:
        """Сохраняет сообщение в историю чата"""
        try:
            data = self._load_data(CHAT_HISTORY_PATH)

            if user_id not in data:
                data[user_id] = []

            data[user_id].append({
                "sender": sender,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })

            self._save_data(CHAT_HISTORY_PATH, data)
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            raise

    def get_history(self, user_id: str) -> List[Dict[str, str]]:
        """Возвращает историю сообщений пользователя"""
        try:
            data = self._load_data(CHAT_HISTORY_PATH)
            return data.get(user_id, [])
        except Exception as e:
            logger.error(f"Error loading chat history: {e}")
            return []

    def save_settings(self, settings: UserSettings) -> None:
        """Сохраняет настройки пользователя"""
        try:
            data = self._load_data(USER_SETTINGS_PATH)
            data[settings.user_id] = settings.dict()
            self._save_data(USER_SETTINGS_PATH, data)
        except Exception as e:
            logger.error(f"Error saving user settings: {e}")
            raise

    def get_settings(self, user_id: str) -> Optional[Dict[str, Union[str, List[str]]]]:
        """Возвращает настройки пользователя"""
        try:
            data = self._load_data(USER_SETTINGS_PATH)
            return data.get(user_id)
        except Exception as e:
            logger.error(f"Error loading user settings: {e}")
            return None

    def update_settings(self, user_id: str, **kwargs) -> bool:
        """Обновляет отдельные поля настроек"""
        try:
            data = self._load_data(USER_SETTINGS_PATH)
            if user_id not in data:
                return False

            for key, value in kwargs.items():
                if key in data[user_id]:
                    data[user_id][key] = value

            self._save_data(USER_SETTINGS_PATH, data)
            return True
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            return False

    def _load_data(self, path: Path) -> dict:
        """Загружает данные из JSON файла"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
        except Exception as e:
            logger.error(f"Error loading data from {path}: {e}")
            raise

    def _save_data(self, path: Path, data: dict) -> None:
        """Сохраняет данные в JSON файл"""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving data to {path}: {e}")
            raise