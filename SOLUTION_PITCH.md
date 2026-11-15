# BhashaMitra — Solution Pitch

> **Speak Your Language. Understand Every Language. Learn Without Limits.**

---

## The Problem

Over 1.3 billion Indians speak one of 22+ scheduled languages — but daily life constantly crosses language boundaries: asking for directions, ordering food, finding a room, talking to customers or neighbors. Existing tools are mostly text-based, support few Indian languages, and none of them *teach* you the language while translating.

## The Solution

**BhashaMitra** is a voice-first multilingual AI assistant. You speak naturally in your own language; the app transcribes you, translates into the language you want, shows the result with pronunciation and meaning — and **speaks it back**. Every translation doubles as a mini language lesson.

No typing. No copying sentences into Google Translate. Just talk.

## How It Works

```text
🎙️ You speak (e.g., Telugu)
        │
        ▼
🧠 Gnani Prisma      → converts speech to text (auto-detects language)
        │
        ▼
🌐 Sarvam Mayura     → translates to target language + Roman pronunciation
        │             (native script & roman output, modern-colloquial mode)
        ▼
🤖 Gemini            → learning layer: English meaning, detected intent,
        │             suggested next sentence, coaching tip
        ▼
🔊 Gnani Timbre      → speaks the translation aloud
        │
        ▼
📱 Beautiful cards: translation · pronunciation · meaning ·
   intent · next sentence · learning tip · audio playback
```

**Speed trick:** the two Sarvam calls and the Gemini call run in parallel, and audio generation happens in a separate request — so the translation appears on screen *before* the voice note is even ready.

## What Makes It Different

| Typical translator | BhashaMitra |
|---|---|
| Text in → text out | **Voice in → voice + text out** |
| Generic output | Translation + pronunciation + meaning + **next sentence + tip** |
| One-shot utility | Builds a personal **learning history** |
| Slow sequential pipeline | **Parallel API calls** — text first, audio streams in |

## Technology

- **Backend:** Python + FastAPI
- **Speech-to-text:** Gnani Prisma (`prisma-v3.0`)
- **Translation:** Sarvam AI Mayura (`mayura:v1`)
- **Learning metadata:** Google Gemini
- **Text-to-speech:** Gnani Timbre (`timbre-v2.5`)
- **Frontend:** HTML/CSS/JS — glassmorphism UI, dark mode, fully responsive

## Supported Languages

🇮🇳 Telugu · Kannada · Hindi · Tamil · English (UI) — backend also supports Bengali, Gujarati, Malayalam, Marathi, Odia, Punjabi.

## Impact

- **Accessibility:** people who can't type in the target script can still communicate.
- **Language preservation:** makes learning Indian languages conversational and low-pressure.
- **Travel & daily life:** auto-rickshaws, hotels, markets, PG hunting — the exact scenarios from real life.

## Try It

- **Live app (local):** `python -m uvicorn app:app --reload` → http://127.0.0.1:8000
- **GitHub:** https://github.com/GollapalliRasmitha/BhashaMitra
- **Demo video:** [add your video link]

---

*Built with Gnani AI, Sarvam AI, and Google Gemini.*
