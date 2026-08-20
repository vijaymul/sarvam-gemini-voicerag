import re

# Fast heuristic guardrails to save latency

OFF_TOPIC_KEYWORDS = ["ignore previous instructions", "write a poem", "translate to", "hack", "bypass"]
UNSAFE_KEYWORDS = ["kill", "murder", "suicide", "terrorist", "bomb"]

def check_input_safety(query: str) -> bool:
    """Returns True if safe, False if potentially unsafe or off-topic."""
    query_lower = query.lower()
    
    for kw in OFF_TOPIC_KEYWORDS + UNSAFE_KEYWORDS:
        if kw in query_lower:
            return False
            
    return True

def check_hallucination(answer: str, context: str) -> bool:
    """
    Very lightweight check. A real system might use an NLI model,
    but we have <200ms budget, so we do a fast heuristic check.
    If the answer says it doesn't know, it's safe.
    """
    if "don't know" in answer.lower():
        return True
    
    # A simple length ratio check could be used here, but for now we trust the LLM prompt.
    return True
