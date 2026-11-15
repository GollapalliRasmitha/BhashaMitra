# BhashaMitra — Demo, Explanation & Submission Pack

---

## 1. Demo Video Script (~2–3 minutes)

Record your screen + voice (OBS, Loom, or phone screen-record). Follow this order:

### 0:00 — Intro (10 sec)
> "Hi, I'm [your name]. Today I'm showing BhashaMitra — a multilingual AI voice translator and language-learning app for Indian languages. The idea is simple: speak in your language, understand and learn another."

### 0:15 — Show the app (20 sec)
- Open http://127.0.0.1:8000
- Point out: pastel design, **From** and **To** language selectors, big microphone button, dark-mode toggle, Learn button.

### 0:35 — Live demo 1: Telugu → Kannada (40 sec)
- Select **From: Telugu**, **To: Kannada**.
- Tap the mic, say **"బాగున్నారా?"**, tap stop.
- Narrate as results appear: *"Watch — the translation card appears first, before the audio finishes. That's because translation and speech generation run in parallel."*
- Point at each card: native Kannada text, Roman pronunciation, English meaning, detected intent, suggested next sentence, learning tip.
- Press **Play** — the Kannada audio plays.

### 1:15 — Live demo 2: Telugu → Hindi (30 sec)
- Swap to **To: Hindi**, say **"మీ పేరు ఏమిటి?"**
- Show: *"आपका नाम क्या है?"* + meaning "What is your name?"

### 1:45 — Features tour (30 sec)
- Click **⇄** swap button.
- Open **📚 Learn** panel — show saved history.
- Toggle **dark mode**.
- (Optional) resize browser to mobile width — show responsive layout.

### 2:15 — How it works (20 sec)
Show this flow (you can draw it or show the README):

```text
Your voice → Gnani Prisma (speech-to-text)
          → Sarvam Mayura (translation + Roman script)
          → Gemini (learning tips — meaning, intent, next sentence)
          → Gnani Timbre (text-to-speech audio)
          → Beautiful cards on screen
```

> *"All processing happens on a FastAPI backend — no API keys in the frontend. Translation returns the moment it's ready; audio streams in separately so you never wait."*

### 2:35 — Close (10 sec)
> "BhashaMitra — speak your language, learn every language. Thanks for watching!"

**Recording tips:** use a quiet room, speak clearly, do a test run first, keep the terminal visible in a corner if you want to show the API logs.

---

## 2. Written Project Explanation

### Problem
India has 22+ scheduled languages and hundreds of millions of people who speak one language but need to communicate in another — for travel, work, or daily life. Existing translators are text-based or support few Indian languages. BhashaMitra lets you simply **speak** and get a spoken + written translation, while also **teaching** you the target language as you go.

### Solution
A web app where you:
1. Pick **From** and **To** languages (Telugu, Kannada, Hindi, Tamil, English).
2. Tap the microphone and speak naturally.
3. Instantly see: the translated sentence, Roman pronunciation, English meaning, detected intent, a suggested next sentence, and a learning tip.
4. Hear the translation spoken aloud.

### Architecture

```text
┌─────────────┐   WAV audio    ┌──────────────────────────────────────┐
│  Browser UI │ ─────────────► │  FastAPI backend (app.py)            │
│  (index.html)│                │                                      │
│             │ ◄───────────── │  1. Gnani Prisma  → transcript       │
│             │   JSON result  │  2. Sarvam Mayura → native + Roman   │
│             │                │     Gemini       → learning metadata │
│             │                │     (steps 2 run in parallel)        │
│             │ ─────────────► │  3. POST /api/tts                    │
│             │   text+lang    │     Gnani Timbre → WAV audio         │
└─────────────┘                └──────────────────────────────────────┘
```

### Key design decisions
- **Translation is authoritative**: `reply_native` and `reply_roman` always come from Sarvam Mayura — Gemini only fills learning metadata and can never change the translation.
- **Speed**: the two Sarvam calls and the Gemini call run in parallel threads; TTS is a separate request so text appears before audio.
- **Honest failures**: if an API fails, the app shows a clear error instead of inventing a fallback translation.
- **No secrets in frontend**: all API keys stay in `.env` on the server.

### Challenges solved
- Gnani Timbre returns WAV files with placeholder header sizes (`0xFFFFFFFF`) — the backend patches real sizes so every browser can play the audio.
- Timbre's API expects audio settings inside an `audio_config` object — an incorrect payload silently returned raw PCM that browsers couldn't decode; fixed per official docs.
- Sarvam Mayura supports `output_script: "roman"` — used to generate pronunciation without a second provider.

---

## 3. Models & APIs Used

| Service | Model / API | Used for | Link |
|---|---|---|---|
| **Gnani AI** | Prisma `prisma-v3.0` | Speech-to-text (Indic languages) | https://docs.gnani.ai/api/STT |
| **Sarvam AI** | Mayura `mayura:v1` (`/translate`) | Translation + Roman transliteration | https://docs.sarvam.ai/api/api-guides-tutorials/models/mayura |
| **Google** | Gemini (`gemini-3.8-flash`) | Learning metadata only (intent, meaning, tips) | https://ai.google.dev/ |
| **Gnani AI** | Timbre `timbre-v2.5` | Text-to-speech | https://docs.gnani.ai/api/TTS/tts-inference |
| **FastAPI** | — | Backend framework | https://fastapi.tiangolo.com/ |

Official Sarvam translation docs: https://docs.sarvam.ai/api/api-reference/text/translate-text

---

## 4. Public Posts — Draft Captions

> Replace `[link]` with your actual post/repo links after publishing.

### LinkedIn post

```text
🚀 Built BhashaMitra — a multilingual AI voice translator + language-learning app for Indian languages.

🗣️ Speak in Telugu → get Kannada/Hindi/Tamil translation with pronunciation, meaning & learning tips — and hear it spoken back.

⚡ Tech: FastAPI · Gnani Prisma (STT) · Sarvam Mayura (translation) · Gemini (learning metadata) · Gnani Timbre (TTS)

✨ Translation appears instantly; audio generates in parallel. Fully responsive, dark mode, learn history.

🔗 GitHub: [link]
🎥 Demo: [link]

#BuildInPublic #IndianLanguages #AIAssistant #FastAPI #SarvamAI #GnaniAI
```

### Instagram caption

```text
Speak your language. Learn every language. 🇮🇳✨

BhashaMitra turns your voice into translation + pronunciation + meaning + speaking practice — for Telugu, Kannada, Hindi, Tamil & English.

Powered by Gnani Prisma, Sarvam Mayura, Gemini & Gnani Timbre.

🔗 GitHub: [link]
🎥 Demo video: [link]

#BhashaMitra #LearnLanguages #IndianTech #AI #VoiceTranslation #BuildInPublic
```

### YouTube / repo description (short)

```text
BhashaMitra — speak in your language, understand and learn another. AI voice translation for Indian languages with pronunciation, meanings and speaking practice. FastAPI + Gnani Prisma + Sarvam Mayura + Gemini + Gnani Timbre.
```

---

## 5. Submission checklist

- [ ] Record the demo video following the script above
- [ ] Upload video (YouTube unlisted / Drive) and paste the link everywhere `[link]` appears
- [ ] Publish the LinkedIn + Instagram posts, then add their URLs to this file or your submission form
- [ ] Keep the GitHub repo public: https://github.com/GollapalliRasmitha/BhashaMitra
- [ ] Do a final test run: Telugu → Kannada, Telugu → Hindi, Telugu → Tamil
