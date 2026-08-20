import asyncio
import io
import sys
import wave
import struct
import math
import httpx

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from backend.app import app

async def run_tests():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        print("1. Testing Health Endpoint:")
        r = await client.get("/api/health")
        print("Health status:", r.status_code)
        assert r.status_code == 200

        print("\n2. Testing Chat RAG Endpoint with User Query:")
        r = await client.post("/api/chat-rag", json={"query": "Hello, how are you? Are you doing any work right now?"})
        print("Chat status:", r.status_code)
        data = r.json()
        print("Answer:", data.get("answer"))
        assert r.status_code == 200
        assert "Error generating response" not in data["answer"]

        print("\n3. Testing Chat RAG Endpoint with Hindi Question:")
        r = await client.post("/api/chat-rag", json={"query": "ताज महल कहाँ स्थित है?"})
        print("Hindi status:", r.status_code)
        data = r.json()
        print("Hindi Answer:", data.get("answer"))
        assert r.status_code == 200

        print("\n4. Testing Voice RAG Endpoint (Mock audio):")
        out = io.BytesIO()
        with wave.open(out, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            for i in range(16000):
                value = int(30000.0 * math.sin(2.0 * math.pi * 440.0 * (i / 16000.0)))
                wav.writeframesraw(struct.pack('<h', value))
        audio_bytes = out.getvalue()
        
        files = {"audio": ("audio.webm", audio_bytes, "audio/webm")}
        r = await client.post("/api/voice-rag", files=files)
        print("Voice status:", r.status_code)
        data = r.json()
        print("Voice answer:", data.get("answer"))
        assert r.status_code == 200

    print("\nAll integration tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(run_tests())
