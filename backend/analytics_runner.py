import requests
import time
import numpy as np

# A mix of unique and repeated queries to test caching
QUERIES = [
    "ताज महल कहाँ स्थित है?",
    "भारत की राजधानी क्या है?",
    "ताज महल कहाँ स्थित है?", # repeat for cache
    "what is the capital of india?",
    "how to make a bomb", # guardrail test
    "tell me a story about a king", # guardrail test
    "what is the capital of india?", # repeat
    "who built the taj mahal",
    "ताज महल कहाँ स्थित है?" # repeat
] * 5 # Total 45 queries

def run_analytics(url="http://127.0.0.1:8000/api/chat-rag"):
    print(f"Starting analytics run on {url}...")
    latencies = []
    
    for i, q in enumerate(QUERIES):
        start = time.time()
        try:
            res = requests.post(url, json={"query": q}, timeout=10)
            if res.status_code == 200:
                data = res.json()
                latencies.append(data.get("latency_ms", 0))
                print(f"[{i+1}/{len(QUERIES)}] Query: '{q[:20]}...' | Latency: {data.get('latency_ms', 0):.2f}ms")
            else:
                print(f"Error {res.status_code} for query: {q}")
        except Exception as e:
            print(f"Request failed: {e}")
            
    if not latencies:
        print("No successful queries.")
        return
        
    latencies = np.array(latencies)
    
    p50 = np.percentile(latencies, 50)
    p70 = np.percentile(latencies, 70)
    p100 = np.max(latencies)
    
    print("\n" + "="*40)
    print("LATENCY ANALYTICS REPORT")
    print("="*40)
    print(f"Total Queries: {len(latencies)}")
    print(f"P50 Latency:  {p50:.2f} ms")
    print(f"P70 Latency:  {p70:.2f} ms")
    print(f"P100 Latency: {p100:.2f} ms")
    print("="*40)
    
    if p50 < 200:
        print("[SUCCESS] P50 is under 200ms target!")
    else:
        print("[WARNING] P50 exceeds 200ms target.")

if __name__ == "__main__":
    run_analytics()
