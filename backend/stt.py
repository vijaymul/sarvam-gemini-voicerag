import os
import httpx
from dotenv import load_dotenv

load_dotenv()

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")

# Persistent async client with connection pooling & keep-alive
_http_client: httpx.AsyncClient | None = None

def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(6.0, connect=3.0),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
        )
    return _http_client

async def transcribe_audio_sarvam(audio_bytes: bytes) -> str:
    """
    Transcribe audio using Sarvam AI STT API.
    Uses persistent httpx client with saaras:v4 model.
    """
    if not audio_bytes or len(audio_bytes) < 100:
        return ""
        
    url = "https://api.sarvam.ai/speech-to-text"
    headers = {
        "api-subscription-key": SARVAM_API_KEY
    }
    
    files = {
        "file": ("audio.webm", audio_bytes, "audio/webm")
    }
    data = {
        "model": "saaras:v4",
        "language_code": "unknown"
    }
    
    client = get_http_client()
    try:
        response = await client.post(url, headers=headers, files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            return result.get("transcript", "").strip()
        else:
            print(f"STT API Warning ({response.status_code}): {response.text}")
            return ""
    except Exception as e:
        print(f"STT Exception: {e}")
        return ""

async def transcribe_audio(audio_bytes: bytes) -> str:
    if not SARVAM_API_KEY or SARVAM_API_KEY == "your_sarvam_api_key_here":
        print("WARNING: Using mock STT because SARVAM_API_KEY is not set.")
        return "ताज महल कहाँ स्थित है" # Where is Taj Mahal (Hindi)
    return await transcribe_audio_sarvam(audio_bytes)


