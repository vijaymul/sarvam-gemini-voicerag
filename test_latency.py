import asyncio
import time
import sys
import numpy as np

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from backend.stt import transcribe_audio
from backend.retrieval import get_context
from backend.generation import generate_answer

MOCK_AUDIO = b"mock_audio_bytes_for_testing"

async def single_run():
    start = time.time()
    
    transcript = await transcribe_audio(MOCK_AUDIO)
    if not transcript:
        transcript = "ताज महल कहाँ स्थित है?"
        
    context = await get_context(transcript)
    answer = await generate_answer(transcript, context)
    
    end = time.time()
    return (end - start) * 1000  # returns ms

async def run_latency_test(iterations=5):
    print(f"Running latency test over {iterations} queries...")
    latencies = []
    
    for i in range(iterations):
        t0 = time.time()
        lat = await single_run()
        latencies.append(lat)
        print(f"Run {i+1}/{iterations}: {lat:.2f} ms")
            
    latencies = np.array(latencies)
    
    p50 = np.percentile(latencies, 50)
    p70 = np.percentile(latencies, 70)
    p100 = np.max(latencies)
    
    print("\n=== Latency Analytics ===")
    print(f"P50  Latency: {p50:.2f} ms")
    print(f"P70  Latency: {p70:.2f} ms")
    print(f"P100 Latency: {p100:.2f} ms")
    print(f"Average     : {np.mean(latencies):.2f} ms")
    print("=========================")

if __name__ == "__main__":
    asyncio.run(run_latency_test(5))
