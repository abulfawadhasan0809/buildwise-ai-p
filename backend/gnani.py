"""Gnani Prisma (STT) and Timbre (TTS) REST clients, per docs.gnani.ai.
Auth header is X-API-Key-ID. The key stays on the server."""
import os, httpx

KEY = lambda: os.getenv("GNANI_API_KEY", "")
STT = lambda: os.getenv("GNANI_STT_URL") or "https://api.vachana.ai/stt/v3"
TTS = lambda: os.getenv("GNANI_TTS_URL") or "https://api.vachana.ai/api/v1/tts/inference"
LANG = lambda: os.getenv("GNANI_LANG", "en-IN")
VOICE = lambda: os.getenv("GNANI_VOICE", "Kaveri")          # a Timbre v2.5 English voice
TTS_MODEL = lambda: os.getenv("GNANI_TTS_MODEL", "timbre-v2.5")

def configured() -> bool:
    return bool(KEY() and KEY() != "your_api_key")

async def transcribe(audio: bytes, filename: str, content_type: str, lang: str | None = None) -> str:
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(STT(), headers={"X-API-Key-ID": KEY()},
                         files={"audio_file": (filename, audio, content_type)},
                         data={"language_code": lang or LANG()})
        if r.status_code >= 400:
            raise RuntimeError(f"{r.status_code} {r.text[:200]}")
        j = r.json()
        return j.get("transcript", "")

async def synthesize(text: str, lang: str | None = None) -> tuple[bytes, str]:
    lang = lang or LANG()
    voice = os.getenv('GNANI_VOICE_' + lang[:2].upper()) or VOICE()  # set GNANI_VOICE_HI etc. to a voice for that language
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(TTS(), headers={"X-API-Key-ID": KEY(), "Content-Type": "application/json"},
                         json={"text": text, "voice": voice, "model": TTS_MODEL(), "language": lang, "speed": 1.0,
                               "audio_config": {"sample_rate": 24000, "num_channels": 1, "sample_width": 2,
                                                "encoding": "linear_pcm", "container": "wav"}})
        if r.status_code >= 400:
            raise RuntimeError(f"{r.status_code} {r.text[:200]}")
        return r.content, r.headers.get("content-type", "audio/wav")