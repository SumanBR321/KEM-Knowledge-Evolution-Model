from sentence_transformers import SentenceTransformer
from typing import List, Dict
import numpy as np

MODEL_NAME = "all-MiniLM-L6-v2"
_model = None

def get_model() -> SentenceTransformer:
    """
    Lazy loads and returns the SentenceTransformer model.
    Model is only loaded on first use to prevent slow starts.
    """
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def generate_embedding(text: str) -> List[float]:
    """
    Generates an embedding for a single text string.
    Returns the embedding as a Python list of floats using .tolist().
    """
    model = get_model()
    # convert_to_numpy=True ensures we get a numpy array back for proper .tolist() conversion
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()

def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generates embeddings for a batch of text strings efficiently.
    Returns a list of Python lists using .tolist() on each generated embedding.
    """
    model = get_model()
    embeddings = model.encode(texts, convert_to_numpy=True, batch_size=32, show_progress_bar=False)
    return [emb.tolist() for emb in embeddings]

def embed_document(processed_data: Dict) -> Dict:
    """
    Takes the full processed_data dict out of text_processing.py output.
    Generates a document-level embedding, and chunk-level embeddings in a single batch.
    Updates the dictionary in place and returns it.
    """
    document_text = processed_data.get("document_text", "")
    
    # Generate document embedding
    # Generate document embedding from a title-prefixed summary representation
    # This ensures document embedding is always distinct from chunk embeddings
    # by creating a high-level semantic signature of the page
    title = processed_data.get("title", "")
    words = document_text.split()
    summary_text = f"{title}. {' '.join(words[:256])}"
    processed_data["document_embedding"] = generate_embedding(summary_text)
    
    # Generate chunk embeddings in a single batch
    chunks = processed_data.get("chunks", [])
    if chunks:
        chunk_texts = [chunk["text"] for chunk in chunks]
        chunk_embeddings = generate_embeddings_batch(chunk_texts)
        
        for chunk, embedding in zip(chunks, chunk_embeddings):
            chunk["embedding"] = embedding
            
    # Print progress
    title = processed_data.get("title", "Unknown")
    print(f"[EMBED] Generated document embedding + {len(chunks)} chunk embeddings for: {title}")

    # Print document embedding preview
    doc_emb = processed_data.get("document_embedding")
    if doc_emb:
        print(f"\n--- DOCUMENT EMBEDDING (dim={len(doc_emb)}) ---")
        print(f"  [{', '.join(f'{v:.6f}' for v in doc_emb[:8])} ...]")

    # Print chunk embeddings preview
    if chunks:
        print(f"\n--- CHUNK EMBEDDINGS ---")
        for chunk in chunks:
            emb = chunk.get("embedding", [])
            if emb:
                print(f"  [{chunk['chunk_id']}] dim={len(emb)} | [{', '.join(f'{v:.6f}' for v in emb[:8])} ...]")
    print("")

    return processed_data
