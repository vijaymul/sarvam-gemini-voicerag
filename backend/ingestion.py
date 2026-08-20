import os
import json
import faiss
import numpy as np
from datasets import load_dataset
from sentence_transformers import SentenceTransformer
import argparse
import time

def semantic_chunking(text, max_tokens=100, overlap=20):
    # Extremely simple token-approximate chunking with overlap
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_tokens - overlap):
        chunk = " ".join(words[i:i + max_tokens])
        if chunk:
            chunks.append(chunk)
    return chunks

def ingest_data(language="hi", max_samples=1000, output_dir="../data"):
    print(f"Loading dataset for {language}...")
    # Loading MSMARCO-XI subset
    # Note: Using 'ai4bharat/MSMARCO-XI'
    # Due to dataset size, we'll only take a subset for the demo
    dataset = load_dataset("ai4bharat/MSMARCO-XI", language, split="train", streaming=True)
    
    print("Loading embedding model...")
    # Fast multilingual model
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    os.makedirs(output_dir, exist_ok=True)
    
    documents = []
    metadata = []
    
    print(f"Processing up to {max_samples} samples...")
    count = 0
    
    start_time = time.time()
    for row in dataset:
        if count >= max_samples:
            break
            
        doc_id = row.get("id", str(count))
        # The dataset might have 'passage' or 'text' depending on structure.
        # Assuming 'passage' is the key based on typical MSMARCO structure.
        # MSMARCO usually has 'query', 'passages'. ai4bharat/MSMARCO-XI has specific schema.
        # Let's extract whatever text is available.
        text = row.get("passage", row.get("text", ""))
        
        if not text:
            continue
            
        chunks = semantic_chunking(text, max_tokens=60, overlap=15)
        for chunk_idx, chunk in enumerate(chunks):
            documents.append(chunk)
            metadata.append({
                "doc_id": doc_id,
                "chunk_idx": chunk_idx,
                "language": language,
                "source": "MSMARCO-XI"
            })
        count += 1
        
    print(f"Created {len(documents)} chunks from {count} documents in {time.time() - start_time:.2f}s")
    
    print("Generating embeddings...")
    start_time = time.time()
    embeddings = model.encode(documents, convert_to_numpy=True)
    print(f"Generated embeddings in {time.time() - start_time:.2f}s")
    
    print("Building FAISS index...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    # Save index and metadata
    faiss.write_index(index, os.path.join(output_dir, f"msmarco_{language}.faiss"))
    with open(os.path.join(output_dir, f"metadata_{language}.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False)
        
    with open(os.path.join(output_dir, f"chunks_{language}.json"), "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False)
        
    print(f"Ingestion complete. Index saved to {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", type=str, default="hi", help="Language code (e.g. hi, ta, te)")
    parser.add_argument("--samples", type=int, default=1000, help="Number of samples to ingest")
    args = parser.parse_args()
    
    ingest_data(args.language, args.samples)
