import os
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

PRIMARY_MODEL_NAME = 'gemini-2.5-flash'

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
        max_output_tokens=1024
    )
    
    last_err = None
    for attempt in range(max_retries):
        try:
            res = await asyncio.wait_for(
                asyncio.to_thread(model.generate_content, prompt, generation_config=gen_config),
                timeout=5.0
            )
            if res and res.candidates:
                candidate = res.candidates[0]
                text_parts = [
                    part.text for part in candidate.content.parts 
                    if hasattr(part, "text") and part.text
                ]
                if text_parts:
                    return "".join(text_parts).strip()
            if hasattr(res, 'text') and res.text:
                return res.text.strip()
        except Exception as e:
            last_err = e
            print(f"Generation attempt {attempt+1} failed: {e}")
            await asyncio.sleep(0.05)
            
    print(f"Gemini generation failed after {max_retries} attempts: {last_err}")
    return "Error generating response. Please check backend logs."

async def generate_answer(query: str, context: str = "") -> str:
    """Generates the final answer using the orchestration harness."""
    if context and context.strip():
        prompt = f"""You are a helpful, fast and accurate AI voice assistant.
Answer the question concisely in 1-2 sentences in the same language as the question.
Use the provided Context as your primary factual source.

Context:
{context}

Question: {query}"""
    else:
        prompt = f"""You are a helpful, fast and accurate AI voice assistant.
Answer the question concisely in 1-2 sentences in the same language as the question.

Question: {query}"""

    # 2. Execute orchestrated call
    ans = await _call_gemini_with_retry(prompt)
    if not ans or "ERR_NO_CONTEXT" in ans:
        return "I'm ready to help. Could you please specify your question?"
        
    return ans
