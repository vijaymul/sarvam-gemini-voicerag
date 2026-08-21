import os
import asyncio
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

async def _call_gemini_with_retry(prompt: str, max_retries: int = 2) -> str:
    """Orchestration Harness: Executes LLM call with retries and ultra-low timeout."""
    if model is None and not GEMINI_API_KEY:
        return "ताज महल उत्तर प्रदेश के आगरा में स्थित है। (Mock Answer - API Key Missing)"
        
    gen_config = genai.types.GenerationConfig(
        candidate_count=1,
        temperature=0.0,
        max_output_tokens=50 # Extremely tight to speed up TTFT
    )
    
    last_err = None
    for attempt in range(max_retries):
        try:
            # Aggressive timeout to ensure we fail fast
            res = await asyncio.wait_for(
                model.generate_content_async(prompt, generation_config=gen_config),
                timeout=1.5
            )
            if hasattr(res, 'text') and res.text:
                return res.text.strip()
        except Exception as e:
            last_err = e
            print(f"Generation attempt {attempt+1} failed: {e}")
            await asyncio.sleep(0.01)
            
    print(f"Gemini generation failed after {max_retries} attempts: {last_err}")
    return "Error generating response. Please check backend logs."

async def generate_answer(query: str, context: str = "") -> str:
    """Generates the final answer using the orchestration harness."""
    
    # 1. Structure the prompt to fail fast on hallucinations
    prompt = f"""You are a helpful, fast voice AI.
Answer the Question using ONLY the Context. Be extremely concise (1-2 sentences).
If the Context does not contain the answer, reply EXACTLY with: ERR_NO_CONTEXT

Context:
{context}

Question: {query}"""

    # 2. Execute orchestrated call
    ans = await _call_gemini_with_retry(prompt)
    
    # 3. Post-Generation Guardrail Check
    if "ERR_NO_CONTEXT" in ans or not ans:
        return "मुझे इस बारे में जानकारी नहीं है। (I do not have enough context to answer this safely)."
        
    return ans
