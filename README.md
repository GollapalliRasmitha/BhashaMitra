# BhashaMitra — భాషా మిత్ర

**Speak Your Language. Understand Every Language. Learn Without Limits.**

BhashaMitra is a multilingual AI voice translation and language-learning assistant for Indian languages. Speak in your own language, and the app transcribes your speech, translates it into the language you choose, shows the translation with Roman pronunciation and English meaning — and speaks it back to you.

## Features

- 🎙️ **Voice input** — record directly from the browser microphone
- 🗣️ **Speech-to-text** — powered by Gnani Prisma (`indic-auto` detection)
- 🌐 **Translation** — powered by Sarvam Mayura (`mayura:v1`, `modern-colloquial`)
- 🔤 **Roman pronunciation** — automatic transliteration of the translated sentence
- 📖 **Language learning** — English meaning, detected intent, suggested next sentence, and coaching tips (Gemini as a metadata helper)
- 🔊 **Text-to-speech** — natural voice playback via Gnani Timbre
- 📚 **Learn panel** — your recent translations saved locally for revision
- 🌙 **Dark / light mode**, fully responsive (mobile, tablet, desktop)
- ⚡ **Fast pipeline** — translation appears as soon as it's ready; audio generates separately

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI |
| Speech-to-text | Gnani Prisma (`prisma-v3.0`) |
| Translation | Sarvam AI Mayura (`mayura:v1`) |
| Learning metadata | Google Gemini |
| Text-to-speech | Gnani Timbre (`timbre-v2.5`) |
| Frontend | HTML, CSS, JavaScript (single `index.html`) |

## Supported languages

Telugu, Kannada, Hindi, Tamil, and English — plus Bengali, Gujarati, Malayalam, Marathi, Odia, and Punjabi are supported by the backend.

## Project structure

```
Gnani/
├── app.py            # FastAPI backend (STT, translation, metadata, TTS, audio serving)
├── index.html        # Complete frontend UI
├── sarvam_test.py    # Minimal Sarvam API smoke test
├── .env              # API keys (never committed)
└── generated_audio/  # Generated TTS audio files
```

## Setup

1. Install dependencies:

```powershell
pip install fastapi uvicorn requests python-dotenv google-genai sarvamai
```

2. Create a `.env` file in the project folder:

```env
GNANI_API_KEY=your_gnani_key
GEMINI_API_KEY=your_gemini_key
SARVAM_API_KEY=your_sarvam_key
```

Get your keys from:
- Gnani AI: https://www.gnani.ai
- Sarvam AI: https://dashboard.sarvam.ai
- Google AI Studio: https://aistudio.google.com

3. Run the server:

```powershell
python -m uvicorn app:app --reload
```

4. Open http://127.0.0.1:8000 in your browser, allow microphone access, pick your languages, and tap the microphone.

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/process-voice` | Audio → transcript → translation + learning metadata (returns immediately, no audio) |
| `POST` | `/api/tts` | Text + language → generated speech (`audio_url`) |
| `GET` | `/audio/{filename}` | Serves generated WAV files |
| `GET` | `/` | The web app |

### `POST /api/process-voice`

Multipart form: `audio` (WAV file), `target_lang`, `source_lang` (optional).

Returns:

```json
{
  "user_said": "-spoken transcript-",
  "detected_lang": "te-IN",
  "ai_reply": {
    "detected_intent": "...",
    "reply_native": "- translation in target script -",
    "reply_roman": "Roman pronunciation",
    "english_meaning": "...",
    "suggested_next_turn_native": "...",
    "suggested_next_turn_roman": "...",
    "coaching_tip": "..."
  },
  "audio_url": null,
  "audio_error": null
}
```

### `POST /api/tts`

JSON body: `{"text": "...", "language": "kn-IN"}` → `{"audio_url": "/audio/....wav"}`

## How it works

```text
Browser mic → Gnani Prisma (STT)
            → Sarvam Mayura native + Roman (parallel)
            → Gemini (learning metadata, parallel)
            → Fast response to browser
            → Gnani Timbre (TTS, separate request)
            → Audio player updates
```

## Notes

- API keys live only in `.env`, which is git-ignored. Never commit them.
- Sarvam Mayura accepts up to 1,000 characters per request.
- If a service fails, the app returns a clear error — it never invents a fallback translation.
