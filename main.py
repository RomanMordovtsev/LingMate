import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from core.models import UserSettings, ChatRequest
from core.history_manager import DatabaseManager
from core.voice_handler import VoiceHandler
from core.config import (
    MENTOR_PROMPT_TEMPLATE,
    GEMINI_CONFIG,
    LEVEL_DESCRIPTIONS,
    TTS_MAX_LENGTH,
    TTS_SUPPORTED_LANGUAGES,
    FALLBACK_LANGUAGE
)
from typing import Dict, Any, Optional
import torch
torch.backends.cudnn.benchmark = True
torch.set_float32_matmul_precision('high')

# Игнорируем предупреждения веса
import warnings
warnings.filterwarnings("ignore",
    message="You are using `torch.load` with `weights_only=False`")
warnings.filterwarnings("ignore",
    message="GPT2InferenceModel has generative capabilities")

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Language Mentor API",
    description="AI Language Learning Assistant with Voice Support",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db = DatabaseManager()
voice = VoiceHandler()

try:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("Gemini API key not found in .env file")

    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel(
        model_name=GEMINI_CONFIG["model_name"],
        generation_config=genai.types.GenerationConfig(
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            max_output_tokens=2000
        ),
        safety_settings=GEMINI_CONFIG["safety_settings"]
    )
    logger.info("Gemini model initialized successfully")
except Exception as e:
    logger.critical(f"Gemini initialization failed: {e}")
    raise RuntimeError("Failed to initialize Gemini API") from e

@app.post("/setup")
async def setup_user(settings: UserSettings) -> Dict[str, Any]:
    try:
        if not settings.target_languages:
            raise HTTPException(status_code=400, detail="At least one target language required")

        db.save_settings(settings)
        return {
            "message": f"Settings saved for user {settings.user_id}",
            "languages": settings.target_languages,
            "level": LEVEL_DESCRIPTIONS.get(settings.level, "Unknown level")
        }
    except Exception as e:
        logger.error(f"Setup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat(request: ChatRequest) -> Dict[str, Any]:
    try:
        settings_data = db.get_settings(request.user_id)
        if not settings_data:
            raise HTTPException(
                status_code=400,
                detail="User settings not found. Please complete setup first."
            )

        settings = UserSettings(**settings_data)

        # Validate languages
        target_lang = settings.target_languages[0]
        native_lang = settings.native_language

        if target_lang not in TTS_MAX_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported target language: {target_lang}"
            )

        if native_lang not in TTS_MAX_LENGTH:
            native_lang = "ru"  # Fallback to Russian

        # Prepare voice parameters
        voice_params = {
            "gender": settings.voice_gender or "female",
            "region": request.voice_region or settings.voice_region,
            "native_lang": native_lang
        }

        # Process history and generate response
        history = db.get_history(request.user_id)
        history_text = "\n".join(
            f"{msg['sender']}: {msg['message']}"
            for msg in history[-10:]  # Limit context window
        )

        prompt = MENTOR_PROMPT_TEMPLATE.format(
            target_language=target_lang,
            native_language=native_lang,
            level=settings.level
        )
        full_input = f"{prompt}\n\nИстория:\n{history_text}\n\nПользователь: {request.message}"

        try:
            response = gemini_model.generate_content(full_input)
            response_text = response.text.strip() if response.text else None

            if not response_text:
                logger.error("Empty response from model")
                response_text = "Извините, не удалось сгенерировать ответ. Пожалуйста, попробуйте еще раз."

        except Exception as e:
            logger.error(f"Model generation failed: {e}")
            response_text = "Произошла ошибка при генерации ответа. Пожалуйста, попробуйте позже."

        # Save messages
        db.save_message(request.user_id, request.message, sender="user")
        db.save_message(request.user_id, response_text, sender="bot")

        # Модифицируем часть в методе chat, где обрабатывается голос:
        voice_success = False
        voice_fallback_used = False

        if request.is_voice and response_text:
            try:
                # Проверяем, будет ли использоваться fallback
                settings = UserSettings(**settings_data)
                if (settings.target_languages[0] not in TTS_SUPPORTED_LANGUAGES or
                        settings.native_language not in TTS_SUPPORTED_LANGUAGES):
                    voice_fallback_used = True

                voice_success = voice.speak_response(
                    text=response_text,
                    target_lang=target_lang,
                    **voice_params
                )
                if not voice_success:
                    logger.warning("Voice generation reported failure")
            except Exception as e:
                logger.error(f"Voice processing failed: {e}")

        return {
            "response": response_text,
            "language": target_lang,
            "voice_processed": request.is_voice and voice_success,
            "voice_fallback_used": voice_fallback_used  # Информируем клиента о fallback
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Chat processing error")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during chat processing"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
