import asyncio
import wave
import math
import struct
from backend.stt import transcribe_audio_sarvam

async def main():
    # Create 1-second sine wave
    import io
    out = io.BytesIO()
    with wave.open(out, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        for i in range(16000):
            value = int(32767.0 * math.sin(2.0 * math.pi * 440.0 * (i / 16000.0)))
            wav.writeframesraw(struct.pack('<h', value))
    
    audio_bytes = out.getvalue()
    print("Audio bytes len:", len(audio_bytes))
    res = await transcribe_audio_sarvam(audio_bytes)
    print("Result:", res)

if __name__ == "__main__":
    asyncio.run(main())
