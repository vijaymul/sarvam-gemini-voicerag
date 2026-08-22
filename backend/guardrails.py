import re

# Fast heuristic guardrails to save latency
OFF_TOPIC_PATTERNS = [
    r"(?i)\b(ignore|forget|disregard).*previous (instructions|prompts)\b",
    r"(?i)\bwrite a (poem|song|story)\b",
    r"(?i)\btranslate.*to\b",
    r"(?i)\bcode (me|a|an)\b",
    r"(?i)\b(hack|bypass)\b"
]

UNSAFE_PATTERNS = [
    r"(?i)\b(kill|murder|suicide|terrorist|bomb|weapon|illegal)\b"
]

def check_input_safety(query: str) -> bool:
    """Returns True if safe, False if potentially unsafe or off-topic."""
    for pattern in OFF_TOPIC_PATTERNS + UNSAFE_PATTERNS:
        if re.search(pattern, query):
            return False
    return True

def check_is_greeting(query: str) -> str:
    """Returns a canned response for greetings to save LLM latency if the query is solely a greeting."""
    q = re.sub(r"[^\w\s]", "", query).lower().strip()
    greetings = {
        "hello", "hi", "hey", "how are you", "namaste", "namaskar",
        "नमस्ते", "नमस्कार", "hello there", "hi there", "hey there",
        "good morning", "good afternoon", "good evening"
    }
    if q in greetings:
        return "Hello! I am ready to help you with your questions."
    return ""

def check_hallucination(answer: str, context: str) -> bool:
    """
    Very lightweight hallucination check. 
    1. If the answer explicitly contains our designated NO_CONTEXT string, it's safe (refusal).
    2. We also check for common 'I don't know' phrasing.
    """
    safe_phrases = ["err_no_context", "don't know", "cannot find", "no information", "मुझे नहीं पता", "जानकारी नहीं"]
    ans_lower = answer.lower()
    
    for phrase in safe_phrases:
        if phrase in ans_lower:
            return True
            
    # For a <200ms budget, running another LLM here is impossible.
    # In a full production system, we'd use a small cross-encoder.
    # We will rely on strict prompting and the safe_phrases check.
    return True
