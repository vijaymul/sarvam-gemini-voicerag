import os
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# High-speed primary model & resilient fallbacks
PRIMARY_MODEL_NAME = 'gemini-3.5-flash-lite'
FALLBACK_MODELS = ['gemini-flash-lite-latest', 'gemini-3.6-flash', 'gemini-2.5-flash']

if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        model = genai.GenerativeModel(PRIMARY_MODEL_NAME)
    except Exception as e:
        print(f"Notice: Initializing {PRIMARY_MODEL_NAME} failed: {e}")
        model = None
else:
    model = None

async def generate_answer(query: str, context: str = "") -> str:
    if model is None and not GEMINI_API_KEY:
        return "ताज महल उत्तर प्रदेश के आगरा में स्थित है। (Mock Answer - API Key Missing)"
        
    if context and context.strip():
        prompt = f"""You are a fast, intelligent, and helpful voice AI assistant.
Answer the user's question clearly, concisely, and accurately based on the context if relevant.
If the query is a greeting, polite conversation, or general query, respond naturally and politely.
Match the language of the user's question (Hindi, English, Hinglish, etc.). Keep the response concise for voice output (1-3 sentences).

Context:
{context}

Question: {query}
Answer:"""
    else:
        prompt = f"""You are a fast, intelligent, and helpful voice AI assistant.
Answer the user's question clearly, politely, and concisely. Keep the response concise for voice output (1-3 sentences).
If the query is a greeting or general conversation, respond warmly and naturally.
Match the language of the user's question (Hindi, English, Hinglish, etc.).

Question: {query}
Answer:"""

    # 1. Try primary fast model with timeout
    if model is not None:
        try:
            gen_config = genai.types.GenerationConfig(
                candidate_count=1,
                temperature=0.3,
                max_output_tokens=150,
            )
            response = await asyncio.wait_for(
                model.generate_content_async(prompt, generation_config=gen_config),
                timeout=4.0
            )
            if hasattr(response, 'text') and response.text:
                return response.text.strip()
            elif response.candidates and response.candidates[0].content.parts:
                return response.candidates[0].content.parts[0].text.strip()
        except Exception as e:
            print(f"Primary model ({PRIMARY_MODEL_NAME}) warning: {e}")

    # 2. Try fast fallbacks
    for fb_name in FALLBACK_MODELS:
        try:
            fb = genai.GenerativeModel(fb_name)
            res = await asyncio.wait_for(
                fb.generate_content_async(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        candidate_count=1,
                        temperature=0.3,
                        max_output_tokens=150,
                    )
                ),
                timeout=4.0
            )
            if hasattr(res, 'text') and res.text:
                return res.text.strip()
            elif res.candidates and res.candidates[0].content.parts:
                return res.candidates[0].content.parts[0].text.strip()
        except Exception as fb_err:
            print(f"Fallback ({fb_name}) warning: {fb_err}")
        
    return "नमस्ते! मैं आपकी क्या सहायता कर सकता हूँ? (Hello! How can I assist you today?)"
