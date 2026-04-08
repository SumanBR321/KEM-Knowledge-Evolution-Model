import os
import numpy as np
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from groq import Groq
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

from services.reranker import rerank_chunks
from services.embedding_service import generate_embedding
from services.vector_store import search_similar

# Constants
MAX_CONTEXT_CHUNKS = 5
INITIAL_RETRIEVAL_K = 15
MODEL_NAME = "llama-3.3-70b-versatile"

# Initialize Groq client
# Ensure GROQ_API_KEY is set in your environment
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def compute_keyword_scores(query: str, chunks: List[Dict]) -> List[float]:
    """
    Computes keyword relevance scores using TF-IDF.

    This helps capture exact term matches that embedding similarity may miss.

    Args:
        query: User query
        chunks: Retrieved chunks

    Returns:
        List of normalized keyword relevance scores
    """
    if not chunks:
        return []
        
    texts = [chunk["text"] for chunk in chunks]

    vectorizer = TfidfVectorizer()
    # Fit on query and chunks
    tfidf_matrix = vectorizer.fit_transform([query] + texts)

    query_vec = tfidf_matrix[0]
    chunk_vecs = tfidf_matrix[1:]

    # Compute dot product for similarity
    scores = (chunk_vecs @ query_vec.T).toarray().flatten()

    # Normalize scores
    max_score = np.max(scores)
    if max_score > 0:
        scores = scores / max_score

    return scores.tolist()

def build_context(chunks: List[Dict]) -> str:
    """
    Builds a structured context string with indexed sources.

    Each chunk is labeled so the LLM can cite sources accurately.

    Returns:
        Formatted context string
    """
    formatted_chunks = []

    for i, chunk in enumerate(chunks, start=1):
        text = chunk.get("text", "")
        url = chunk.get("url", "unknown")

        formatted_chunks.append(
            f"[{i}] Source: {url}\n{text}"
        )

    return "\n\n---\n\n".join(formatted_chunks)

def query_knowledge(user_query: str) -> Dict[str, Any]:
    """
    End-to-end RAG pipeline:
    1. Embed query
    2. Initial semantic retrieval
    3. Hybrid scoring (semantic + keyword)
    4. Reranking (Cross-encoder)
    5. Context formatting
    6. LLM Generation
    """
    
    # 1. Generate query embedding
    query_embedding = generate_embedding(user_query)

    # 2. Initial semantic search
    initial_chunks = search_similar(
        query_embedding,
        n_results=INITIAL_RETRIEVAL_K
    )

    if not initial_chunks:
        return {
            "status": "no_results",
            "message": "No relevant pages found in your knowledge base"
        }

    # 3. Compute keyword scores
    keyword_scores = compute_keyword_scores(user_query, initial_chunks)

    # 4. Combine scores for Hybrid Search
    for i, chunk in enumerate(initial_chunks):
        embedding_score = chunk.get("score", 0)
        keyword_score = keyword_scores[i]

        chunk["hybrid_score"] = (0.7 * embedding_score) + (0.3 * keyword_score)

    # 5. Sort by hybrid score
    hybrid_ranked = sorted(
        initial_chunks,
        key=lambda x: x["hybrid_score"],
        reverse=True
    )

    # 6. Rerank top candidates using Cross-Encoder
    top_candidates = hybrid_ranked[:INITIAL_RETRIEVAL_K]
    reranked_chunks = rerank_chunks(user_query, top_candidates)

    # 7. Final selection
    chunks = reranked_chunks[:MAX_CONTEXT_CHUNKS]

    # 8. Build context for LLM
    context = build_context(chunks)

    # 9. LLM Generation
    system_prompt = """You are a personal knowledge assistant for KEM: Knowledge Evolution Model.

You must answer questions ONLY using the provided context from the user's saved pages.

STRICT RULES:
- Do NOT use prior knowledge.
- Do NOT make assumptions.
- If the answer is not fully supported by the context, explicitly say:
  "I don't have enough information from your saved knowledge to answer this fully."
- Always ground your response in the provided sources.

CITATIONS:
- When using information from a source, cite it using:
  [1], [2], etc.
- At the end of your answer, include:

Sources:
[1] <url>
[2] <url>

Be precise, factual, and concise."""

    user_prompt = f"Context:\n{context}\n\nQuery: {user_query}"

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
        )
        response_text = completion.choices[0].message.content
    except Exception as e:
        print(f"Error during LLM generation: {e}")
        return {
            "status": "error",
            "message": "Failed to generate answer from knowledge base."
        }

    # 10. Format final response
    return {
        "status": "success",
        "query": user_query,
        "answer": response_text,
        "sources": list(set(chunk["url"] for chunk in chunks)),
        "chunks_used": len(chunks)
    }
