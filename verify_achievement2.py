import requests
import json

test_data = {
    "title": "Achievement 2 Test",
    "url": "http://verification.test",
    "timestamp": "2026-03-12T21:50:00Z",
    "content": "This is a test document for achievement 2. We are verifying the cleaning and chunking logic. Cookie policy: we use cookies. This sentence should be removed as boilerplate. The rest of the content is useful for knowledge evolution modeling. " * 50
}

print("Simulating processing for Achievement 2 verification...")
from services.text_processing import process_page_data
result = process_page_data(test_data)

print("\n--- Verification Summary ---")
print(f"Chunks Created: {len(result['chunks'])}")
print(f"Cleaned Text Sample: {result['document_text'][:100]}...")
if len(result['chunks']) > 0:
    print("✓ Text Processing Pipeline: OK")
else:
    print("✗ Text Processing Pipeline: FAILED")
