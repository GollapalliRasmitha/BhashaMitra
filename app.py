
import os
import json
import struct
import uuid
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pydantic import BaseModel
from google import genai
from google.genai import types
from dotenv import load_dotenv


# Load .env from the same folder as this app.py
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

GNANI_API_KEY = os.getenv("GNANI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

AUDIO_DIR = BASE_DIR / "generated_audio"
AUDIO_DIR.mkdir(exist_ok=True)

app = FastAPI(title="BhashaMitra")


SYSTEM_PROMPT = """
You are BhashaMitra's language-learning coach.

The user's sentence has already been translated by Sarvam Mayura.
Do NOT translate the sentence yourself and do NOT change the supplied
translation. Only produce the learning metadata below.

Return ONLY valid JSON with exactly these fields:
{
  "detected_intent": "Short description of the user's intention",
  "english_meaning": "English meaning of the original sentence",
  "suggested_next_turn_native": "One useful next sentence in the target language for the scenario",
  "suggested_next_turn_roman": "Romanized pronunciation of that suggested sentence",
  "coaching_tip": "One short language-learning tip"
}
"""


SARVAM_TRANSLATE_URL = "https://api.sarvam.ai/translate"
SARVAM_TIMEOUT_SECONDS = 30

# Languages supported by Sarvam Mayura (mayura:v1)
MAYURA_LANGUAGES = {
    "bn-IN", "en-IN", "gu-IN", "hi-IN", "kn-IN", "ml-IN",
    "mr-IN", "od-IN", "pa-IN", "ta-IN", "te-IN",
}


class SarvamAPIError(Exception):
    def __init__(self, message, status_code=502, details=""):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


def normalize_language_code(code):
    code = (code or "").strip()
    if not code or code.lower() in ("unknown", "auto"):
        return ""
    code = code.replace("_", "-")
    parts = code.split("-")
    lang = parts[0].lower()
    region = parts[1].upper() if len(parts) > 1 else "IN"
    return f"{lang}-{region}"


def sarvam_translate(text, source_language_code, target_language_code, output_script,
                     mode="modern-colloquial"):
    payload = {
        "input": text,
        "source_language_code": source_language_code,
        "target_language_code": target_language_code,
        "model": "mayura:v1",
        "mode": mode,
        "output_script": output_script,
    }
    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json",
    }

    try:
        res = requests.post(
            SARVAM_TRANSLATE_URL,
            json=payload,
            headers=headers,
            timeout=SARVAM_TIMEOUT_SECONDS,
        )
    except requests.exceptions.Timeout:
        raise SarvamAPIError(
            "Sarvam translation timed out. Please try again.",
            status_code=504,
        )
    except requests.exceptions.RequestException as e:
        print(f"[Sarvam Network Error]: {e}")
        raise SarvamAPIError(
            "Could not connect to Sarvam translation. Check your internet connection.",
            status_code=503,
        )

    print(f"[Sarvam Status]: {res.status_code}")
    print(f"[Sarvam Response]: {res.text[:1500]}")

    if res.status_code in (401, 403):
        raise SarvamAPIError(
            "Sarvam API key is invalid or unauthorized. Check SARVAM_API_KEY in your .env file.",
            status_code=502,
            details=res.text[:1000],
        )
    if res.status_code == 429:
        raise SarvamAPIError(
            "Sarvam rate limit reached. Please wait a moment and try again.",
            status_code=429,
            details=res.text[:1000],
        )
    if res.status_code == 400:
        raise SarvamAPIError(
            "Sarvam rejected the translation request. The language pair or input may be unsupported.",
            status_code=400,
            details=res.text[:1000],
        )
    if res.status_code != 200:
        raise SarvamAPIError(
            f"Sarvam translation failed ({res.status_code}).",
            status_code=502,
            details=res.text[:1000],
        )

    try:
        return res.json()
    except ValueError:
        raise SarvamAPIError(
            "Sarvam returned an unreadable translation response.",
            status_code=502,
        )


def fetch_learning_metadata(user_transcript, target_lang, scenario, source_lang):
    """Call Gemini for learning metadata only. Never raises; returns {} on failure."""
    if not gemini_client:
        return {}

    prompt = f"""
Original transcript: {user_transcript}
Target language code: {target_lang}
Detected source language code: {source_lang}
Conversation scenario (only for the suggested next sentence): {scenario}

Produce only the learning metadata JSON described in the system instructions.
"""
    try:
        ai_response = gemini_client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0.2
            )
        )

        if not ai_response or not ai_response.text:
            raise ValueError("Gemini returned an empty response.")

        parsed = json.loads(ai_response.text)
        if not isinstance(parsed, dict):
            raise ValueError("Gemini returned invalid metadata.")
        return parsed

    except Exception as e:
        print(f"[Gemini Metadata Error]: {type(e).__name__}: {e}")
        return {}


def assemble_learning_data(metadata, user_transcript, reply_native, reply_roman, source_lang):
    """Merge Gemini metadata with the Sarvam translation into the final 7-field reply."""
    english_meaning = ""
    if isinstance(metadata.get("english_meaning"), str):
        english_meaning = metadata["english_meaning"].strip()

    normalized_source = normalize_language_code(source_lang)
    if not english_meaning:
        if normalized_source == "en-IN":
            english_meaning = user_transcript
        else:
            try:
                meaning_result = sarvam_translate(
                    text=user_transcript,
                    source_language_code=normalized_source or "auto",
                    target_language_code="en-IN",
                    output_script="fully-native",
                )
                english_meaning = (meaning_result.get("translated_text") or "").strip()
            except SarvamAPIError as e:
                print(f"[English Meaning Fallback Error]: {e.message}")

    def clean(field):
        value = metadata.get(field)
        return value.strip() if isinstance(value, str) else ""

    return {
        "detected_intent": clean("detected_intent") or english_meaning or "Unable to determine intent",
        "reply_native": reply_native,
        "reply_roman": reply_roman,
        "english_meaning": english_meaning or "English meaning unavailable.",
        "suggested_next_turn_native": clean("suggested_next_turn_native"),
        "suggested_next_turn_roman": clean("suggested_next_turn_roman"),
        "coaching_tip": clean("coaching_tip") or "Learning suggestions are temporarily unavailable.",
    }


@app.post("/api/process-voice")
async def process_voice(
    audio: UploadFile = File(...),
    target_lang: str = Form("te-IN"),
    source_lang: str = Form(""),
    scenario: str = Form("")
):
    with open(BASE_DIR / "debug_log.txt", "a", encoding="utf-8") as f:
     f.write("[DEBUG] Voice request received!\n")
    if not GNANI_API_KEY:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Gnani API key is missing. Check GNANI_API_KEY in your .env file."
            }
        )

    if not SARVAM_API_KEY:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Sarvam API key is missing. Check SARVAM_API_KEY in your .env file."
            }
        )

    target_lang = normalize_language_code(target_lang)
    if target_lang not in MAYURA_LANGUAGES:
        return JSONResponse(
            status_code=400,
            content={
                "error": f"Unsupported target language: {target_lang or 'empty'}. "
                         "Sarvam Mayura supports: bn-IN, en-IN, gu-IN, hi-IN, kn-IN, "
                         "ml-IN, mr-IN, od-IN, pa-IN, ta-IN, te-IN."
            }
        )

    requested_source = normalize_language_code(source_lang)
    if requested_source and requested_source not in MAYURA_LANGUAGES:
        return JSONResponse(
            status_code=400,
            content={
                "error": f"Unsupported source language: {requested_source}. "
                         "Sarvam Mayura supports: bn-IN, en-IN, gu-IN, hi-IN, kn-IN, "
                         "ml-IN, mr-IN, od-IN, pa-IN, ta-IN, te-IN."
            }
        )

    if not gemini_client:
        print("[Gemini Client Available]: False - learning metadata will use fallback values")

    audio_bytes = await audio.read()

    if not audio_bytes:
        return JSONResponse(
            status_code=400,
            content={"error": "The recorded audio is empty. Please record again."}
        )

    # Start total processing timer
    total_start = time.perf_counter()

    # 1. Speech-to-Text using Gnani Prisma
    stt_start = time.perf_counter()

    stt_url = "https://api.vachana.ai/stt/v3"
    stt_headers = {"X-API-Key-ID": GNANI_API_KEY}
    stt_files = {
        "audio_file": ("recording.wav", audio_bytes, "audio/wav")
    }
    stt_data = {
        "model": "prisma-v3.0",
        "language_code": "indic-auto"
    }

    print(f"\n[STT Request] Sending {len(audio_bytes)} bytes to Gnani Prisma...")

    try:
        stt_res = requests.post(
            stt_url,
            headers=stt_headers,
            files=stt_files,
            data=stt_data,
            timeout=30
        )

    except requests.exceptions.Timeout:
        return JSONResponse(
            status_code=504,
            content={
                "error": "Gnani speech recognition timed out. Please try again."
            }
        )

    except requests.exceptions.RequestException as e:
        print(f"[STT Network Error]: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "error": "Could not connect to Gnani speech recognition. Check your internet connection."
            }
        )

    print(f"[TIME] Prisma: {time.perf_counter() - stt_start:.2f} seconds")

    print(f"[STT Status]: {stt_res.status_code}")
    print(f"[STT Response]: {stt_res.text[:1500]}")

    if stt_res.status_code != 200:
        return JSONResponse(
            status_code=502,
            content={
                "error": f"Gnani speech recognition failed ({stt_res.status_code}).",
                "details": stt_res.text[:1000]
            }
        )

    try:
        stt_data = stt_res.json()

    except ValueError:
        return JSONResponse(
            status_code=502,
            content={
                "error": "Gnani returned an unreadable speech-recognition response."
            }
        )

    user_transcript = (stt_data.get("transcript") or "").strip()

    if not user_transcript:
        return JSONResponse(
            status_code=400,
            content={
                "error": "No speech detected. Please speak clearly and try again."
            }
        )

    print(f"[Transcript]: {user_transcript}")
    print(f"[Gemini Client Available]: {gemini_client is not None}")

    if len(user_transcript) > 1000:
        return JSONResponse(
            status_code=400,
            content={
                "error": "The transcript is too long for Sarvam Mayura (maximum 1000 characters)."
            }
        )

    # 2. Translate the actual transcript using Sarvam Mayura
    sarvam_start = time.perf_counter()

    detected_source = normalize_language_code(stt_data.get("detected_language_code"))
    if requested_source:
        source_lang = requested_source
    else:
        source_lang = detected_source if detected_source in MAYURA_LANGUAGES else "auto"

    # English sources get formal mode so Mayura doesn't code-mix English
    # words into the target language; Indic sources stay colloquial.
    effective_source = requested_source or detected_source
    translation_mode = "formal" if effective_source == "en-IN" else "modern-colloquial"

    try:
        # Run the two Sarvam calls and the Gemini metadata call in parallel
        # so the user waits for the slowest one, not the sum of all three.
        with ThreadPoolExecutor(max_workers=3) as pool:
            native_future = pool.submit(
                sarvam_translate,
                text=user_transcript,
                source_language_code=source_lang,
                target_language_code=target_lang,
                output_script="fully-native",
                mode=translation_mode,
            )
            roman_future = pool.submit(
                sarvam_translate,
                text=user_transcript,
                source_language_code=source_lang,
                target_language_code=target_lang,
                output_script="roman",
                mode=translation_mode,
            )
            meta_future = pool.submit(
                fetch_learning_metadata,
                user_transcript=user_transcript,
                target_lang=target_lang,
                scenario=scenario,
                source_lang=source_lang,
            )

            native_result = native_future.result()
            roman_result = roman_future.result()
            metadata = meta_future.result()

        reply_native = (native_result.get("translated_text") or "").strip()
        if not reply_native:
            raise SarvamAPIError("Sarvam returned an empty translation.", status_code=502)

        reply_roman = (roman_result.get("translated_text") or "").strip()
        if not reply_roman:
            raise SarvamAPIError("Sarvam returned an empty Roman transliteration.", status_code=502)

    except SarvamAPIError as e:
        print(f"[Sarvam Error]: {e.message} | {e.details}")
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": e.message,
                "details": e.details[:1000] if e.details else ""
            }
        )

    sarvam_source_lang = (
        normalize_language_code(native_result.get("source_language_code"))
        or (source_lang if source_lang != "auto" else "")
    )

    print(f"[TIME] Sarvam+Gemini (parallel): {time.perf_counter() - sarvam_start:.2f} seconds")

    # 3. Merge learning metadata with the Sarvam translation.
    ai_data = assemble_learning_data(
        metadata=metadata,
        user_transcript=user_transcript,
        reply_native=reply_native,
        reply_roman=reply_roman,
        source_lang=sarvam_source_lang or "auto",
    )

    print("[Final Reply]:", json.dumps(ai_data, ensure_ascii=False))

    # Audio is generated separately via /api/tts so the translation
    # can be shown to the user as soon as it is ready.
    print(f"[TIME] Total: {time.perf_counter() - total_start:.2f} seconds")

    return {
        "user_said": user_transcript,
        "detected_lang": sarvam_source_lang or stt_data.get("detected_language_code") or "unknown",
        "ai_reply": ai_data,
        "audio_url": None,
        "audio_error": None
    }


def synthesize_timbre(text, language):
    """Generate speech with Gnani Timbre. Returns (audio_url, error_message)."""
    tts_url = "https://api.vachana.ai/api/v1/tts/inference"

    tts_payload = {
        "text": text,
        "language": language,
        "voice": "Kaveri",
        "model": "timbre-v2.5",
        "speed": 0.85,
        "audio_config": {
            "sample_rate": 24000,
            "num_channels": 1,
            "sample_width": 2,
            "encoding": "linear_pcm",
            "container": "wav"
        }
    }

    try:
        tts_res = requests.post(
            tts_url,
            json=tts_payload,
            headers={
                "X-API-Key-ID": GNANI_API_KEY,
                "Content-Type": "application/json"
            },
            timeout=45
        )

        print(f"[TTS Status]: {tts_res.status_code}")

        if tts_res.status_code == 200 and tts_res.content:
            audio_bytes = tts_res.content

            # Timbre returns a WAV header with placeholder sizes (0xFFFFFFFF).
            # Patch them so every browser can read the file correctly.
            if (len(audio_bytes) >= 44
                    and audio_bytes[:4] == b"RIFF"
                    and audio_bytes[36:40] == b"data"
                    and struct.unpack("<I", audio_bytes[40:44])[0] == 0xFFFFFFFF):
                audio_bytes = (
                    audio_bytes[:4]
                    + struct.pack("<I", len(audio_bytes) - 8)
                    + audio_bytes[8:40]
                    + struct.pack("<I", len(audio_bytes) - 44)
                    + audio_bytes[44:]
                )

            audio_filename = f"reply_{uuid.uuid4().hex}.wav"
            audio_path = AUDIO_DIR / audio_filename

            audio_path.write_bytes(audio_bytes)

            return f"/audio/{audio_filename}", None

        print(f"[TTS Error]: {tts_res.text[:1000]}")
        return None, f"Gnani Timbre failed ({tts_res.status_code})."

    except requests.exceptions.Timeout:
        print("[TTS Network Error]: timed out")
        return None, "Speech generation timed out. Please try again."

    except requests.exceptions.RequestException as e:
        print(f"[TTS Network Error]: {e}")
        return None, "Could not connect to Gnani Timbre. Check your internet connection."


class TtsRequest(BaseModel):
    text: str
    language: str = "te-IN"


@app.post("/api/tts")
async def generate_tts(req: TtsRequest):
    if not GNANI_API_KEY:
        return JSONResponse(
            status_code=500,
            content={"error": "Gnani API key is missing. Check GNANI_API_KEY in your .env file."}
        )

    text = (req.text or "").strip()
    if not text:
        return JSONResponse(status_code=400, content={"error": "Text is empty."})

    language = normalize_language_code(req.language)
    if language not in MAYURA_LANGUAGES:
        return JSONResponse(
            status_code=400,
            content={"error": f"Unsupported language for speech generation: {language or 'empty'}."}
        )

    tts_start = time.perf_counter()
    audio_url, error = synthesize_timbre(text, language)
    print(f"[TIME] Timbre: {time.perf_counter() - tts_start:.2f} seconds")

    if audio_url:
        return {"audio_url": audio_url, "audio_error": None}

    return {
        "audio_url": None,
        "audio_error": error or "Speech generation failed. Check the server terminal for the TTS error."
    }


@app.get("/audio/{filename}")
def serve_audio(filename: str):
    # Prevent path traversal and serve only generated audio files
    safe_name = Path(filename).name
    audio_path = AUDIO_DIR / safe_name

    if safe_name != filename or not audio_path.is_file():
        return JSONResponse(
            status_code=404,
            content={"error": "Audio file not found."}
        )

    return FileResponse(
        audio_path,
        media_type="audio/wav",
        filename=safe_name
    )



@app.get("/")
def index():
    return FileResponse(BASE_DIR / "index.html")
