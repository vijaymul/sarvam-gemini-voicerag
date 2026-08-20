import os
import json
import faiss
import numpy as np
from datasets import load_dataset
from sentence_transformers import SentenceTransformer
import argparse
import time

import re

def recursive_character_split(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """
    Advanced chunking: splits by paragraphs, then sentences, then words to respect semantics.
    """
    separators = ["\n\n", "\n", ". ", " ", ""]
    
    def split_recursively(text_to_split: str, sep_index: int) -> list[str]:
        if len(text_to_split) <= chunk_size:
            return [text_to_split]
            
        separator = separators[sep_index] if sep_index < len(separators) else ""
        
        # Split the text
        if separator:
            splits = text_to_split.split(separator)
        else:
            splits = list(text_to_split)
            
        # Merge splits
        chunks = []
        current_chunk = ""
        
        for s in splits:
            part = s + (separator if s and separator else "")
            if len(current_chunk) + len(part) <= chunk_size:
                current_chunk += part
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # If a single split is still too large, we recurse on it
                if len(part) > chunk_size and sep_index + 1 < len(separators):
                    sub_chunks = split_recursively(part, sep_index + 1)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = part
                    
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks

    # Generate initial chunks
    raw_chunks = split_recursively(text, 0)
    
    # Handle Overlap
    final_chunks = []
    for i, rc in enumerate(raw_chunks):
        if not rc.strip(): continue
        
        if i == 0:
            final_chunks.append(rc)
        else:
            # Prepend overlap from previous chunk
            prev = final_chunks[-1]
            overlap_text = prev[-chunk_overlap:] if len(prev) > chunk_overlap else prev
            # Try to find a clean break for the overlap (e.g. space)
            space_idx = overlap_text.find(" ")
            if space_idx != -1 and space_idx < len(overlap_text) - 1:
                overlap_text = overlap_text[space_idx+1:]
                
            merged = (overlap_text + " " + rc).strip()
            # If merging makes it way too big, just use rc. Otherwise, use merged.
            if len(merged) > chunk_size + chunk_overlap:
                final_chunks.append(rc)
            else:
                final_chunks.append(merged)
                
    return final_chunks

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
            
        chunks = recursive_character_split(text, chunk_size=300, chunk_overlap=30)
        for chunk_idx, chunk in enumerate(chunks):
            documents.append(chunk)
            metadata.append({
                "doc_id": doc_id,
                "chunk_idx": chunk_idx,
                "language": language,
                "source": "ai4bharat/MSMARCO-XI",
                "length": len(chunk),
                "is_first_chunk": chunk_idx == 0,
                "is_last_chunk": chunk_idx == len(chunks) - 1
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
