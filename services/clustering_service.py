import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from typing import List, Dict, Any, Optional
from services.vector_store import get_collections

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIN_DOCS_FOR_CLUSTERING = 3
MAX_CLUSTERS = 8
MIN_CLUSTERS = 2


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_optimal_k(embeddings: np.ndarray) -> int:
    """
    Determine the optimal number of KMeans clusters using silhouette score.

    The silhouette score measures how similar each point is to its own cluster
    compared to other clusters (range: -1 to +1; higher is better). We try
    every integer k in [MIN_CLUSTERS, min(MAX_CLUSTERS, n-1)] and return the k
    that maximises the silhouette score, ensuring the most semantically
    coherent grouping without over-fragmenting the data.

    Parameters
    ----------
    embeddings : np.ndarray
        2-D array of shape (n_documents, embedding_dim).

    Returns
    -------
    int
        Optimal number of clusters.  Returns 1 if there are fewer than
        MIN_DOCS_FOR_CLUSTERING documents (no meaningful clustering possible).
    """
    n = len(embeddings)

    if n < MIN_DOCS_FOR_CLUSTERING:
        return 1

    k_max = min(MAX_CLUSTERS, n - 1)
    k_candidates = list(range(MIN_CLUSTERS, k_max + 1))

    # Only one valid k — no need to compare
    if len(k_candidates) == 1:
        return k_candidates[0]

    best_k = k_candidates[0]
    best_score = -1.0

    for k in k_candidates:
        kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
        labels = kmeans.fit_predict(embeddings)
        score = silhouette_score(embeddings, labels)
        if score > best_score:
            best_score = score
            best_k = k

    return best_k


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------

def cluster_documents() -> Dict[str, Any]:
    """
    Cluster all stored documents by semantic similarity using KMeans.

    Fetches every document embedding from ChromaDB, determines the optimal
    number of clusters via silhouette score, runs KMeans, and returns a
    structured summary of which documents belong to each concept cluster.

    Returns
    -------
    dict
        On success::

            {
                "status": "success",
                "cluster_count": int,
                "document_count": int,
                "clusters": {
                    0: {"cluster_id": 0, "document_count": n, "documents": [...]},
                    ...
                }
            }

        When there are too few documents::

            {
                "status": "insufficient_data",
                "message": str,
                "document_count": int
            }
    """
    documents_collection, _ = get_collections()

    result = documents_collection.get(include=["embeddings", "metadatas"])
    ids       = result["ids"]
    embeddings = result["embeddings"]
    metadatas  = result["metadatas"]

    n = len(ids)

    if n < MIN_DOCS_FOR_CLUSTERING:
        return {
            "status": "insufficient_data",
            "message": f"Need at least {MIN_DOCS_FOR_CLUSTERING} saved pages to cluster",
            "document_count": n,
        }

    embeddings_array = np.array(embeddings)

    k = get_optimal_k(embeddings_array)

    kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
    labels = kmeans.fit_predict(embeddings_array)

    # Build cluster buckets
    clusters: Dict[int, Dict[str, Any]] = {}
    for cluster_id in range(k):
        clusters[cluster_id] = {
            "cluster_id":     cluster_id,
            "document_count": 0,
            "documents":      [],
        }

    for label, meta in zip(labels, metadatas):
        cluster_id = int(label)
        clusters[cluster_id]["documents"].append({
            "title":     meta.get("title", ""),
            "url":       meta.get("url", ""),
            "timestamp": meta.get("timestamp", ""),
        })
        clusters[cluster_id]["document_count"] += 1

    print(f"[CLUSTER] Found {k} concept clusters across {n} documents")

    return {
        "status":         "success",
        "cluster_count":  k,
        "document_count": n,
        "clusters":       clusters,
    }


def get_reinforced_concepts() -> Dict[str, Any]:
    """
    Identify the most reinforced concept cluster from saved documents.

    "Concept reinforcement" reflects repeated user interest: the cluster with
    the highest document count represents the topic the user has visited most
    often, making it the strongest signal of a knowledge anchor in the
    Knowledge Evolution Model.

    Returns
    -------
    dict
        On success::

            {
                "status": "success",
                "reinforced_cluster_id": int,
                "reinforced_document_count": int,
                "reinforced_documents": list[dict],
                "all_clusters": dict
            }

        Passes through the ``insufficient_data`` response from
        ``cluster_documents()`` unchanged when there are too few documents.
    """
    result = cluster_documents()

    if result["status"] != "success":
        return result

    clusters = result["clusters"]

    # Find the cluster with the most documents
    reinforced_id = max(clusters, key=lambda cid: clusters[cid]["document_count"])
    reinforced_cluster = clusters[reinforced_id]

    return {
        "status":                    "success",
        "reinforced_cluster_id":     reinforced_id,
        "reinforced_document_count": reinforced_cluster["document_count"],
        "reinforced_documents":      reinforced_cluster["documents"],
        "all_clusters":              clusters,
    }
