from flask import Flask, request, jsonify
from flask_cors import CORS
from services.text_processing import process_page_data

app = Flask(__name__)
# Enable CORS for requests from the Chrome Extension
CORS(app)

@app.route('/save_page', methods=['POST'])
def save_page():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid input, JSON required"}), 400
        
    raw_content = data.get('content', '')
    input_text_length = len(raw_content)
    
    # Run preprocessing pipeline
    processed_data = process_page_data(data)
    
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
        "data": processed_data
    })

if __name__ == '__main__':
    print("Starting Knowledge Memory Backend on http://localhost:5000")
    print("Listening for POST requests on /save_page...")
    app.run(port=5000, debug=True)
