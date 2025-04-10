from typing import List, Literal, Optional
from pydantic import BaseModel

class UserSettings(BaseModel):
    user_id: str
    target_languages: List[str]
    native_language: str = "ru"
    voice_gender: Literal["male", "female"] = "female"
    voice_region: Optional[str] = None  # Новое поле для акцента/региона
    level: Literal["A1", "A2", "B1", "B2", "C1", "C2"] = "A1"
    interests: List[str] = []
    active: bool = True

class ChatRequest(BaseModel):
    user_id: str
    message: str
    is_voice: bool = False
    voice_region: Optional[str] = None  # Переопределение региона для конкретного запроса