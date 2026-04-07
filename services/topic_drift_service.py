import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any
from collections import defaultdict
from datetime import datetime
from services.vector_store import get_collections

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DRIFT_THRESHOLD_HIGH   = 0.4
DRIFT_THRESHOLD_MEDIUM = 0.2


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def get_week_key(timestamp_str: str) -> str:
    """
    Convert an ISO 8601 timestamp string to a 'YYYY-WXX' week identifier.

    The function normalises the trailing 'Z' timezone marker (used in
    JavaScript / ChromeDB timestamps) to '+00:00' so that
    ``datetime.fromisoformat`` can parse it correctly on Python 3.10 and
    earlier, where the 'Z' suffix is not yet supported.

    Parameters
    ----------
    timestamp_str : str
        An ISO 8601 datetime string, e.g. ``'2024-03-15T10:23:45Z'`` or
        ``'2024-03-15T10:23:45+00:00'``.

    Returns
    -------
    str
        A string in the format ``'YYYY-WXX'``, e.g. ``'2024-W11'``,
        representing the ISO week number of the given timestamp.
    """
    normalised = timestamp_str.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalised)
    return dt.strftime("%Y-W%W")


def compute_centroid(embeddings: List[List[float]]) -> np.ndarray:
    """
    Compute the centroid (mean vector) of a list of embedding vectors.

    The centroid is the element-wise arithmetic mean across all provided
    vectors and acts as a single representative point for the semantic
    "centre of mass" of the group.

    Parameters
    ----------
    embeddings : list of list of float
        A non-empty list of embedding vectors, all with the same
        dimensionality.

    Returns
    -------
    np.ndarray
        A 1-D array of shape ``(embedding_dim,)`` representing the centroid.
    """
    arr = np.array(embeddings)
    return arr.mean(axis=0)


def compute_drift_label(distance: float) -> str:
    """
    Map a cosine distance value to a human-readable drift severity label.

    The thresholds are defined by the module-level constants
    ``DRIFT_THRESHOLD_HIGH`` (0.4) and ``DRIFT_THRESHOLD_MEDIUM`` (0.2).

    Parameters
    ----------
    distance : float
        Cosine distance between two weekly centroids (range 0 – 2, but
        typically 0 – 1 for normalised embeddings).

    Returns
    -------
    str
        One of:
        - ``'high drift'``     — distance > DRIFT_THRESHOLD_HIGH
        - ``'moderate drift'`` — distance > DRIFT_THRESHOLD_MEDIUM
        - ``'stable'``         — distance ≤ DRIFT_THRESHOLD_MEDIUM
    """
    if distance > DRIFT_THRESHOLD_HIGH:
        return "high drift"
    if distance > DRIFT_THRESHOLD_MEDIUM:
        return "moderate drift"
    return "stable"


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def detect_topic_drift() -> Dict[str, Any]:
    """
    Detect temporal knowledge drift across weekly windows of saved pages.

    Algorithm — Temporal Centroid Approach
    ----------------------------------------
    1. Retrieve every document from the ChromaDB ``kem_documents`` collection,
       including its embedding vector and metadata (title, url, timestamp).
    2. Group documents by the ISO week they were saved (``YYYY-WXX`` key)
       using :func:`get_week_key`.
    3. For each week, compute a single *centroid* embedding with
       :func:`compute_centroid`.  The centroid summarises the dominant
       semantic direction of all pages read during that week.
    4. For every consecutive pair of weekly centroids, measure the
       *cosine distance* (1 − cosine_similarity).  A distance close to 0
       means the user's reading topics barely changed; a distance near 1
       means they pivoted to an entirely different subject domain.
    5. Label each transition with a drift severity via :func:`compute_drift_label`.
    6. Summarise the series with average drift, maximum drift, and an
       overall trend (``'diverging'`` / ``'converging'`` / ``'stable'``).

    Returns
    -------
    dict
        One of three shapes depending on data availability:

        **Insufficient data** (< 2 documents)::

            {
                "status":  "insufficient_data",
                "message": "Need at least 2 saved pages to detect drift"
            }

        **Single week** (all docs in the same week)::

            {
                "status":         "single_window",
                "message":        "...",
                "weeks":          ["2024-W11"],
                "document_count": 5
            }

        **Success**::

            {
                "status":           "success",
                "week_count":       3,
                "document_count":   12,
                "weekly_centroids": {"2024-W11": 4, "2024-W12": 5, ...},
                "drift_analysis":   [
                    {
                        "from_week":      "2024-W11",
                        "to_week":        "2024-W12",
                        "cosine_distance": 0.3142,
                        "drift_label":    "moderate drift",
                        "from_doc_count": 4,
                        "to_doc_count":   5
                    },
                    ...
                ],
                "summary": {
                    "average_drift": 0.2891,
                    "max_drift":     0.4103,
                    "trend":         "diverging"
                }
            }
    """
    documents_collection, _ = get_collections()

    result = documents_collection.get(include=["embeddings", "metadatas"])

    embeddings = result.get("embeddings")
    metadatas  = result.get("metadatas")

    if embeddings is None: embeddings = []
    if metadatas is None: metadatas = []

    total_docs = len(embeddings)

    # --- Guard: need at least 2 documents ---
    if total_docs < 2:
        return {
            "status":  "insufficient_data",
            "message": "Need at least 2 saved pages to detect drift",
        }

    # --- Group embeddings by week ---
    weekly_embeddings: Dict[str, List[List[float]]] = defaultdict(list)

    for emb, meta in zip(embeddings, metadatas):
        timestamp = meta.get("timestamp", "")
        if not timestamp:
            continue
        week_key = get_week_key(timestamp)
        weekly_embeddings[week_key].append(emb)

    # --- Sort weeks chronologically ---
    sorted_weeks = sorted(weekly_embeddings.keys())

    # --- Guard: need at least 2 distinct weeks ---
    if len(sorted_weeks) < 2:
        return {
            "status":         "single_window",
            "message":        "Need pages from at least 2 different weeks to detect drift",
            "weeks":          sorted_weeks,
            "document_count": total_docs,
        }

    # --- Compute one centroid per week ---
    weekly_centroids: Dict[str, np.ndarray] = {
        week: compute_centroid(weekly_embeddings[week])
        for week in sorted_weeks
    }

    # --- Compute drift between consecutive weekly centroids ---
    drift_analysis = []

    for i in range(len(sorted_weeks) - 1):
        week_a = sorted_weeks[i]
        week_b = sorted_weeks[i + 1]

        centroid_a = weekly_centroids[week_a].reshape(1, -1)
        centroid_b = weekly_centroids[week_b].reshape(1, -1)

        distance = 1.0 - cosine_similarity(centroid_a, centroid_b)[0][0]
        label    = compute_drift_label(distance)

        drift_analysis.append({
            "from_week":       week_a,
            "to_week":         week_b,
            "cosine_distance": round(float(distance), 4),
            "drift_label":     label,
            "from_doc_count":  len(weekly_embeddings[week_a]),
            "to_doc_count":    len(weekly_embeddings[week_b]),
        })

    # --- Summarise ---
    all_distances  = [d["cosine_distance"] for d in drift_analysis]
    average_drift  = round(float(np.mean(all_distances)), 4)
    max_drift      = round(float(np.max(all_distances)),  4)

    first_distance = all_distances[0]
    last_distance  = all_distances[-1]

    if last_distance > first_distance:
        trend = "diverging"
    elif last_distance < first_distance:
        trend = "converging"
    else:
        trend = "stable"

    print(
        f"[DRIFT] Analysed {len(sorted_weeks)} weeks of knowledge "
        f"— trend: {trend}"
    )

    return {
        "status":           "success",
        "week_count":       len(sorted_weeks),
        "document_count":   total_docs,
        "weekly_centroids": {
            week: len(weekly_embeddings[week]) for week in sorted_weeks
        },
        "drift_analysis": drift_analysis,
        "summary": {
            "average_drift": average_drift,
            "max_drift":     max_drift,
            "trend":         trend,
        },
    }
