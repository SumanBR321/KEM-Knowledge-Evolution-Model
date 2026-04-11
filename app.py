from dotenv import load_dotenv
load_dotenv()
from flask import Flask, request, jsonify
from flask_cors import CORS
from services.text_processing import process_page_data
from services.embedding_service import embed_document
from services.vector_store import save_page as store_page
from services.clustering_service import cluster_documents, get_reinforced_concepts
from services.topic_drift_service import detect_topic_drift
from services.rag_service import query_knowledge

app = Flask(__name__)
# Enable CORS for requests from the Chrome Extension
CORS(
    app,
    resources={r"/query": {"origins": "*"}},
    methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type"]
)

@app.route('/save_page', methods=['POST'])
def save_page():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid input, JSON required"}), 400
        
    raw_content = data.get('content', '')
    input_text_length = len(raw_content)
    
    # Run preprocessing pipeline
    processed_data = process_page_data(data)
    processed_data = embed_document(processed_data)
    store_result = store_page(processed_data)
    print(f"[STORE] Status: {store_result['status']} | Document ID: {store_result.get('document_id', 'N/A')[:8]}...")
    
    cleaned_text_length = len(processed_data['document_text'])
    num_chunks = len(processed_data['chunks'])
    
    # Logging (Step 9)
    print("\n=======================================")
    print("📄 NEW PAGE EXTRACTED & PROCESSED")
    print("=======================================")
    print(f"Title: {processed_data['title']}")
    print(f"URL:   {processed_data['url']}")
    print(f"Time:  {processed_data['timestamp']}")
    print("---------------------------------------")
    print(f"Received page content length: {input_text_length} characters")
    print(f"Cleaned text length: {cleaned_text_length} characters")
    print(f"Chunks created: {num_chunks}")
    print(f"Embeddings generated: document + {num_chunks} chunk embeddings")
    
    if num_chunks > 0:
        print("\n--- CHUNKS PREVIEW ---")
        for chunk in processed_data['chunks']:
            preview = chunk['text'][:500] + "...\n" if len(chunk['text']) > 500 else chunk['text'] + "\n"
            print(f"[{chunk['chunk_id']}] {preview}")
            print("-" * 50)
    
    print("=======================================\n")
    
    # Return response (Step 8)
    return jsonify({
        "status": "processed",
        "chunks_created": num_chunks,
        "document_id": store_result.get("document_id"),
        "data": processed_data
    })

@app.route('/get_clusters', methods=['GET'])
def get_clusters():
    """Returns concept clusters from all saved documents."""
    result = cluster_documents()
    return jsonify(result)

@app.route('/get_reinforced_concepts', methods=['GET'])
def reinforced_concepts():
    """Returns the most reinforced concept cluster."""
    result = get_reinforced_concepts()
    return jsonify(result)

@app.route('/get_topic_drift', methods=['GET'])
def topic_drift():
    """Returns temporal knowledge drift analysis across weekly windows."""
    result = detect_topic_drift()
    return jsonify(result)

@app.route('/query', methods=['POST', 'OPTIONS'])
def query():
    """Queries saved knowledge and returns grounded answers."""
    # 0. Handle CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
    # 1. Method validation
    if request.method != 'POST':
        return jsonify({
            "status": "error",
            "message": "Method not allowed. Use POST."
        }), 405

    # 2. Content-Type validation
    if not request.is_json:
        return jsonify({
            "status": "error",
            "message": "Content-Type must be application/json"
        }), 400

    # 3. Existing validation
    data = request.json
    if not data or 'query' not in data:
        return jsonify({
            "status": "error",
            "message": "query field required"
        }), 400
        
    user_query = data.get('query', '').strip()
    result = query_knowledge(user_query)
    return jsonify(result)

@app.route('/get_stats', methods=['GET'])
def get_stats():
    """Returns high-level knowledge base statistics."""
    from services.vector_store import get_collections
    from services.clustering_service import cluster_documents
    
    documents_col, chunks_col = get_collections()
    
    doc_data = documents_col.get(include=["metadatas"])
    total_docs = len(doc_data["ids"])
    total_chunks = len(chunks_col.get()["ids"])
    
    recent_docs = []
    if doc_data["metadatas"]:
        sorted_docs = sorted(
            zip(doc_data["ids"], doc_data["metadatas"]),
            key=lambda x: x[1].get("timestamp", ""),
            reverse=True
        )
        recent_docs = [
            {"document_id": did[:8], "title": meta.get("title"), 
             "url": meta.get("url"), "timestamp": meta.get("timestamp")}
            for did, meta in sorted_docs[:5]
        ]
    
    return jsonify({
        "status": "success",
        "total_documents": total_docs,
        "total_chunks": total_chunks,
        "recent_saves": recent_docs
    })

@app.route('/get_contradictions', methods=['GET'])
def contradictions():
    """Detects potentially conflicting information across saved pages."""
    from services.topic_drift_service import detect_contradictions
    result = detect_contradictions()
    return jsonify(result)

if __name__ == '__main__':
    print("Starting Knowledge Memory Backend on http://localhost:5000")
    print("Listening for POST requests on /save_page...")
    app.run(port=5000, debug=True)
