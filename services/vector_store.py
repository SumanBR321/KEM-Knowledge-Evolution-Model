import chromadb
from chromadb.config import Settings
from typing import Dict, Any, List, Optional
import uuid
import os

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CHROMA_DB_PATH = "./chroma_db"
DOCUMENTS_COLLECTION = "kem_documents"
CHUNKS_COLLECTION = "kem_chunks"

# Module-level client — lazily initialised on first use
_client = None


# ---------------------------------------------------------------------------
# Client & collection helpers
# ---------------------------------------------------------------------------

def get_client():
    """
    Return the shared ChromaDB PersistentClient, creating it on first call.

    Uses lazy initialisation so the database connection is only opened when
    it is actually needed, rather than at import time.
    """
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    return _client


def get_collections():
    """
    Return (documents_collection, chunks_collection), creating them if they
    do not yet exist.

    - ``kem_documents``: one vector per page — the full-document embedding.
      Used for document-level retrieval and metadata look-ups.
    - ``kem_chunks``: one vector per text chunk — used for fine-grained
      semantic search within pages.

    Both collections use cosine distance (``hnsw:space = cosine``).
    """
    client = get_client()

    documents_collection = client.get_or_create_collection(
        name=DOCUMENTS_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )
    chunks_collection = client.get_or_create_collection(
        name=CHUNKS_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )

    return documents_collection, chunks_collection


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------

def save_page(processed_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Persist a processed page (document + its chunks) to ChromaDB.

    Parameters
    ----------
    processed_data : dict
        Output from the embedding pipeline. Expected keys:
        ``title``, ``url``, ``timestamp``, ``word_count``,
        ``document_embedding``, ``chunks``.

    Returns
    -------
    dict
        ``{"status": "saved", "document_id": <uuid>, "chunks_stored": <int>}``
        on success, or ``{"status": "error", "message": <str>}`` on failure.
    """
    documents_collection, chunks_collection = get_collections()

    document_id = str(uuid.uuid4())

    # --- Extract fields from processed data ---
    title              = processed_data.get("title", "")
    url                = processed_data.get("url", "")
    timestamp          = processed_data.get("timestamp", "")
    word_count         = processed_data.get("word_count", 0)
    document_embedding = processed_data.get("document_embedding")
    chunks             = processed_data.get("chunks", [])

    # --- Guard: document embedding is required ---
    if document_embedding is None:
        print("[STORE] WARNING: No document embedding found — skipping save.")
        return {"status": "error", "message": "No embedding found"}

    # --- Store the document-level vector ---
    documents_collection.add(
        ids=[document_id],
        embeddings=[document_embedding],
        metadatas=[{
            "title":      title,
            "url":        url,
            "timestamp":  timestamp,
            "word_count": word_count,
        }],
    )

    # --- Store each chunk vector ---
    for chunk in chunks:
        if chunk.get("embedding") is None:
            continue  # skip chunks that failed to embed

        chunk_store_id = str(uuid.uuid4())

        chunks_collection.add(
            ids=[chunk_store_id],
            embeddings=[chunk["embedding"]],
            documents=[chunk["text"]],
            metadatas=[{
                "chunk_id":    chunk["chunk_id"],
                "url":         url,
                "timestamp":   timestamp,
                "document_id": document_id,
            }],
        )

    print(
        f"[STORE] Saved document {document_id[:8]}... "
        f"with {len(chunks)} chunks — {title}"
    )

    return {
        "status":        "saved",
        "document_id":   document_id,
        "chunks_stored": len(chunks),
    }


def search_similar(
    query_embedding: List[float],
    n_results: int = 5,
) -> List[Dict]:
    """
    Find the *n_results* most semantically similar chunks for a query vector.

    Parameters
    ----------
    query_embedding : list[float]
        The embedding of the search query (same dimensionality as stored
        chunk embeddings).
    n_results : int, optional
        Number of nearest neighbours to return (default: 5).

    Returns
    -------
    list[dict]
        Each dict contains: ``text``, ``url``, ``timestamp``,
        ``document_id``, ``distance``.
    """
    _, chunks_collection = get_collections()

    results = chunks_collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    formatted = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        formatted.append({
            "text":        doc,
            "url":         meta.get("url", ""),
            "timestamp":   meta.get("timestamp", ""),
            "document_id": meta.get("document_id", ""),
            "distance":    dist,
            "score":       1.0 - dist  # Include score for hybrid retrieval
        })

    return formatted


def get_all_documents() -> List[Dict]:
    """
    Retrieve metadata for every document stored in ChromaDB.

    Returns
    -------
    list[dict]
        Each dict contains: ``document_id``, ``title``, ``url``,
        ``timestamp``, ``word_count``.
    """
    documents_collection, _ = get_collections()

    result = documents_collection.get(include=["metadatas"])

    documents = []
    for doc_id, meta in zip(result["ids"], result["metadatas"]):
        documents.append({
            "document_id": doc_id,
            "title":       meta.get("title", ""),
            "url":         meta.get("url", ""),
            "timestamp":   meta.get("timestamp", ""),
            "word_count":  meta.get("word_count", 0),
        })

    return documents
