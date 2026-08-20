import time

class FastCache:
    def __init__(self):
        # Maps query_text -> (answer, context, timestamp)
        self.exact_cache = {}
        
    def get(self, query: str):
        query_lower = query.strip().lower()
        if query_lower in self.exact_cache:
            entry = self.exact_cache[query_lower]
            print(f"CACHE HIT for query: {query}")
            return entry[0], entry[1]
        return None, None
        
    def set(self, query: str, answer: str, context: str):
        query_lower = query.strip().lower()
        self.exact_cache[query_lower] = (answer, context, time.time())

# Singleton
semantic_cache = FastCache()
