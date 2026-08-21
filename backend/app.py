from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import time
import asyncio
import os

from backend.stt import transcribe_audio
from backend.retrieval import get_context
from backend.generation import generate_answer
from backend.guardrails import check_input_safety

app = FastAPI(title="Voice RAG API - HH Goa 2026")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RAGResponse(BaseModel):
    transcript: str
    context: str
    answer: str
    latency_ms: float
    stt_latency_ms: float = 0.0
    retrieval_latency_ms: float = 0.0
    generation_latency_ms: float = 0.0

class ChatRequest(BaseModel):
    query: str

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Voice RAG Backend is healthy and running"}

@app.post("/api/voice-rag", response_model=RAGResponse)
async def process_voice_rag(audio: UploadFile = File(...)):
    start_time = time.time()
    
    # 1. Read audio bytes
    audio_bytes = await audio.read()
    
    # 2. STT
    stt_start = time.time()
    transcript = await transcribe_audio(audio_bytes)
    stt_latency = (time.time() - stt_start) * 1000
    
    if not transcript or not transcript.strip():
        return RAGResponse(
            transcript="",
            context="",
            answer="No audible speech was detected. Please hold the button, speak into your microphone, and release.",
            latency_ms=(time.time() - start_time) * 1000,
            stt_latency_ms=stt_latency,
            retrieval_latency_ms=0.0,
            generation_latency_ms=0.0
        )
        
    # 3. Guardrail (Input)
    if not check_input_safety(transcript):
        return RAGResponse(
            transcript=transcript,
            context="",
            answer="I'm sorry, I cannot process that request as it violates safety policies.",
            latency_ms=(time.time() - start_time) * 1000,
            stt_latency_ms=stt_latency,
            retrieval_latency_ms=0.0,
            generation_latency_ms=0.0
        )
        
    # 4. Check Cache
    from backend.cache import semantic_cache
    cached_ans, cached_ctx = semantic_cache.get(transcript)
    if cached_ans:
        return RAGResponse(
            transcript=transcript,
            context=cached_ctx,
            answer=cached_ans,
            latency_ms=round((time.time() - start_time) * 1000, 2),
            stt_latency_ms=stt_latency,
            retrieval_latency_ms=0.0,
            generation_latency_ms=0.0
        )
        
    # 4.5 Check Greeting
    from backend.guardrails import check_is_greeting
    greeting = check_is_greeting(transcript)
    if greeting:
        return RAGResponse(
            transcript=transcript,
            context="Greeting bypass (0ms latency)",
            answer=greeting,
            latency_ms=round((time.time() - start_time) * 1000, 2),
            stt_latency_ms=round(stt_latency, 2),
            retrieval_latency_ms=0.0,
            generation_latency_ms=0.0
        )
        
    # 5. Retrieval
    ret_start = time.time()
    context = await get_context(transcript)
    ret_latency = (time.time() - ret_start) * 1000
    
    # 6. Generation
    gen_start = time.time()
    answer = await generate_answer(transcript, context)
    gen_latency = (time.time() - gen_start) * 1000
    
    # Save to cache
    semantic_cache.set(transcript, answer, context)
    
    # Calculate Latency
    total_latency = (time.time() - start_time) * 1000
    
    return RAGResponse(
        transcript=transcript,
        context=context,
        answer=answer,
        latency_ms=round(total_latency, 2),
        stt_latency_ms=round(stt_latency, 2),
        retrieval_latency_ms=round(ret_latency, 2),
        generation_latency_ms=round(gen_latency, 2)
    )

@app.post("/api/chat-rag", response_model=RAGResponse)
async def process_chat_rag(req: ChatRequest):
    start_time = time.time()
    query = req.query.strip()
    
    if not query:
        return RAGResponse(
            transcript="",
            context="",
            answer="Please enter a question.",
            latency_ms=0.0
        )
        
    if not check_input_safety(query):
        return RAGResponse(
            transcript=query,
            context="",
            answer="I'm sorry, I cannot process that request as it violates safety policies.",
            latency_ms=(time.time() - start_time) * 1000
        )
        
    # 4. Check Cache
    from backend.cache import semantic_cache
    cached_ans, cached_ctx = semantic_cache.get(query)
    if cached_ans:
        return RAGResponse(
            transcript=query,
            context=cached_ctx,
            answer=cached_ans,
            latency_ms=round((time.time() - start_time) * 1000, 2),
            stt_latency_ms=0.0,
            retrieval_latency_ms=0.0,
            generation_latency_ms=0.0
        )
        
    # 4.5 Check Greeting
    from backend.guardrails import check_is_greeting
    greeting = check_is_greeting(query)
    if greeting:
        return RAGResponse(
            transcript=query,
            context="Greeting bypass (0ms latency)",
            answer=greeting,
            latency_ms=round((time.time() - start_time) * 1000, 2),
            stt_latency_ms=0.0,
            retrieval_latency_ms=0.0,
            generation_latency_ms=0.0
        )
        
    # Retrieval
    ret_start = time.time()
    context = await get_context(query)
    ret_latency = (time.time() - ret_start) * 1000
    
    # Generation
    gen_start = time.time()
    answer = await generate_answer(query, context)
    gen_latency = (time.time() - gen_start) * 1000
    
    # Save to cache
    semantic_cache.set(query, answer, context)
    
    total_latency = (time.time() - start_time) * 1000
    
    return RAGResponse(
        transcript=query,
        context=context,
        answer=answer,
        latency_ms=round(total_latency, 2),
        stt_latency_ms=0.0,
        retrieval_latency_ms=round(ret_latency, 2),
        generation_latency_ms=round(gen_latency, 2)
    )

# Serve the static frontend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_dir = os.path.join(BASE_DIR, "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
def serve_frontend():
    index_file = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Voice RAG API"}

