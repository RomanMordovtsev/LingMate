    # LingMate  
**AI Language Learning Assistant with Voice Support**

## 🧠 Project Logic

1. **Goal**:  
   Simulate a “native-speaking friend” who:
   - Communicates in the target language  
   - Provides translations in the native language  
   - Analyzes mistakes and suggests content (songs, videos)

2. **Features**:
   - Voice synthesis (XTTS v2)  
   - Scalable across languages  
   - Duolingo-like reminders  
   - Level adaptation (A1–C2)  
   - Learns from textbooks and media content  
   - Supports accents and dialects  

---

## 📂 Code Structure

| File/Folder               | Description                                       |
|---------------------------|---------------------------------------------------|
| `convert_audio.py`        | Converts audio format from `.mp3` to `.wav`       |
| `requirements.txt`        | Required dependencies                             |
| `core/models.py`          | Pydantic models (user settings, requests)         |
| `core/voice_handler.py`   | Text-to-speech, audio queue handling              |
| `core/history_manager.py` | Stores chat history and settings (as JSON)        |
| `core/config.py`          | Configuration: prompts, TTS, difficulty levels    |
| `main.py`                 | FastAPI server + Gemini integration               |
| `start_server.bat`        | Startup script for Windows                        |

---

## 🔧 How to Run

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your Gemini API key:
   ```ini
   GEMINI_API_KEY=your_key_here
   ```

3. Start the server:
   ```bash
   python main.py
   ```

   Or run `start_server.bat` on Windows.

---

## 🌍 Supported Languages

**TTS (Speech synthesis):**
1. English (en)  
2. Spanish (es)  
3. French (fr)  
4. German (de)  
5. Italian (it)  
6. Portuguese (pt)  
7. Polish (pl)  
8. Turkish (tr)  
9. Russian (ru)  
10. Dutch (nl)  
11. Czech (cs)  
12. Arabic (ar)  
13. Chinese (Simplified, zh-ccn)  
14. Hungarian (hu)  
15. Korean (ko)  
16. Japanese (ja)  
17. Hindi (hi)

**Text/Translation**: Any language (via Gemini)  
**Note**: If the native language is not supported by TTS, it falls back to Russian.

---

## 📌 Known Issues & TODO

- Improve prompts for more accurate translations  
- Add TTS support for Lithuanian, Urdu, and other languages  
- Integrate YouTube/TikTok API for content recommendations  
- Integrate textbooks for structured learning alongside informal conversation

    
