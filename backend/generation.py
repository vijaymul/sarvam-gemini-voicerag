import os
import asyncio
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# We use the absolute fastest model available on the Gemini API to hit <200ms
PRIMARY_MODEL_NAME = 'gemini-1.5-flash-8b'

if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        model = genai.GenerativeModel(PRIMARY_MODEL_NAME)
    except Exception as e:
        print(f"Notice: Initializing {PRIMARY_MODEL_NAME} failed: {e}")
        model = None
else:
    model = None

async def _call_gemini_with_retry(prompt: str, max_retries: int = 2) -> dict:
    """Orchestration Harness: Executes LLM call with structured output constraints and retries."""
    if model is None and not GEMINI_API_KEY:
        return {"answer": "ताज महल उत्तर प्रदेश के आगरा में स्थित है। (Mock Answer - API Key Missing)", "is_grounded": True}
        
    gen_config = genai.types.GenerationConfig(
        candidate_count=1,
        temperature=0.1,
        max_output_tokens=60, # Extremely tight to speed up TTFT and total latency
        response_mime_type="application/json"
    )
    
    last_err = None
    for attempt in range(max_retries):
        try:
            # Aggressive timeout to ensure we fail fast and fallback
            res = await asyncio.wait_for(
                model.generate_content_async(prompt, generation_config=gen_config),
                timeout=2.0
            )
            if hasattr(res, 'text') and res.text:
                return json.loads(res.text.strip())
        except Exception as e:
            last_err = e
            print(f"Generation attempt {attempt+1} failed: {e}")
            await asyncio.sleep(0.05)
            
    print(f"Gemini generation failed after {max_retries} attempts: {last_err}")
    return {"answer": "Error generating response. Please check backend logs.", "is_grounded": False}

async def generate_answer(query: str, context: str = "") -> str:
    """Generates the final answer using the structured orchestration harness."""
    
    # 1. Structure the prompt to ask for strictly JSON to satisfy harness requirements
    prompt = f"""You are a fast, intelligent voice AI assistant.
Respond strictly in JSON: {{"answer": "concise answer", "is_grounded": boolean (true if context supports it or if it's a general greeting, false if you are hallucinating or guessing)}}

Context:
{context}

Question: {query}"""

    # 2. Execute orchestrated call
    data = await _call_gemini_with_retry(prompt)
    
    # 3. Post-Generation Guardrail Check
    if not data.get("is_grounded", True):
        # Fail safe if the model flags its own hallucination
        return "मुझे इस बारे में जानकारी नहीं है। (I do not have enough context to answer this safely)."
        
    ans = data.get("answer", "")
    if not ans:
        return "नमस्ते! मैं आपकी क्या सहायता कर सकता हूँ?"
        
    return ans
