from sentence_transformers import CrossEncoder
from typing import List, Dict

# Explicitly load the model
model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def rerank_chunks(query: str, chunks: List[Dict]) -> List[Dict]:
    """
    Reranks retrieved chunks using a cross-encoder model.

    This improves retrieval accuracy by evaluating query–chunk pairs
    with deep semantic understanding instead of vector similarity alone.

    Args:
        query: User query string
        chunks: List of retrieved chunks

    Returns:
        List of chunks sorted by relevance (highest first)
    """
    if not chunks:
        return []

    # Prepare pairs for the CrossEncoder
    pairs = [(query, chunk["text"]) for chunk in chunks]
    
    # Predict relevance scores
    scores = model.predict(pairs)

    # Combine chunks with their scores and rank
    ranked = sorted(
        zip(chunks, scores),
        key=lambda x: x[1],
        reverse=True
    )

    # Return the chunks in ranked order
    return [chunk for chunk, _ in ranked]
