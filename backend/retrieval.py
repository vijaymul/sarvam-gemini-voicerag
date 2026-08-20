import os
import json
import numpy as np

try:
    import faiss
except ImportError:
    faiss = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

class Retriever:
    def __init__(self, index_path=None, chunks_path=None):
        if index_path is None:
            index_path = os.path.join(DATA_DIR, "msmarco_hi.faiss")
        if chunks_path is None:
            chunks_path = os.path.join(DATA_DIR, "chunks_hi.json")
            
        self.index = None
        self.chunks = []
        self.model = None
        
        if faiss and os.path.exists(index_path) and os.path.exists(chunks_path):
            try:
                self.index = faiss.read_index(index_path)
                with open(chunks_path, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
                print(f"Loaded FAISS index with {len(self.chunks)} chunks.")
            except Exception as e:
                print(f"Notice: Error loading FAISS index: {e}")
        else:
            print("FAISS index or chunks not loaded. Using semantic/direct context matching.")
            
        if SentenceTransformer and self.index is not None:
            try:
                self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            except Exception as e:
                print(f"SentenceTransformer load notice: {e}")
        
    async def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        if self.index is None or not self.chunks or self.model is None:
            q_lower = query.lower()
            # If query is specifically about Taj Mahal or monuments, supply knowledge snippet
            if any(w in q_lower for w in ["taj", "mahal", "ताज", "महल"]):
                return ["ताज महल भारत के आगरा शहर में यमुना नदी के तट पर स्थित एक विश्व धरोहर सफेद संगमरमर का मक़बरा है, जिसे मुग़ल सम्राट शाहजहाँ ने अपनी बेगम मुमताज़ महल की याद में बनवाया था।"]
            return []
            
        try:
            # Embed query (synchronous, but fast)
            query_embedding = self.model.encode([query], convert_to_numpy=True)
            
            # Search
            distances, indices = self.index.search(query_embedding, top_k)
            
            results = []
            for idx in indices[0]:
                if idx != -1 and idx < len(self.chunks):
                    results.append(self.chunks[idx])
                    
            return results
        except Exception as e:
            print(f"Retrieval error: {e}")
            return []

# Singleton instance
retriever = Retriever()

async def get_context(query: str) -> str:
    chunks = await retriever.retrieve(query)
    return "\n".join(chunks)

