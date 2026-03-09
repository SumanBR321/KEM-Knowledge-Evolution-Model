import re
from typing import Dict, Any, List
from langchain_text_splitters import RecursiveCharacterTextSplitter

def clean_text(raw_text: str) -> str:
    """
    Clean raw webpage text by removing excessive whitespace,
    repeated line breaks, and unnecessary characters.
    """
    if not raw_text:
        return ""
    
    # replace newline characters with space
    text = raw_text.replace('\n', ' ').replace('\r', ' ')
    
    # replace multiple spaces with one
    text = re.sub(r' +', ' ', text)
    
    # trim leading and trailing spaces
    return text.strip()

def remove_boilerplate(text: str) -> str:
    """
    Remove boilerplate noise such as cookie policies, 
    advertisements, and navigation links.
    """
    if not text:
        return ""
        
    noise_patterns = [
        r'(?i)cookie policy',
        r'(?i)advertisement',
        r'(?i)subscribe',
        r'(?i)login(?! to)', # naive check
        r'(?i)navigation',
        r'(?i)footer links'
    ]
    
    # Split text into sentences to remove boilerplate at a sentence level
    sentences = re.split(r'(?<=[.!?])\s+', text)
    filtered = []
    
    for sentence in sentences:
        if not any(re.search(p, sentence) for p in noise_patterns):
            filtered.append(sentence)
            
    # Joining it back
    return ' '.join(filtered).strip()

def chunk_document(document_text: str, source_url: str, timestamp: str) -> List[Dict[str, str]]:
    """
    Split document-level text into semantic chunks optimized for transformer models.
    chunk_size = 400-500 words
    chunk_overlap = 50 words
    """
    if not document_text:
        return []
        
    def word_length(text: str) -> int:
        return len(text.split())
        
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=450,
        chunk_overlap=50,
        length_function=word_length,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunk_texts = splitter.split_text(document_text)
    
    chunks = []
    for i, ct in enumerate(chunk_texts):
        chunks.append({
            "chunk_id": f"chunk_{i+1}",
            "text": ct.strip(),
            "url": source_url,
            "timestamp": timestamp
        })
        
    return chunks

def process_page_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Full text preprocessing pipeline for Knowledge Memory.
    """
    raw_text = data.get('content', '')
    title = data.get('title', '')
    url = data.get('url', '')
    timestamp = data.get('timestamp', '')
    
    print("\n[PROCESS] Raw text length:", len(raw_text))
    
    # Step 2: Clean text
    cleaned_basic = clean_text(raw_text)
    print("\n[PROCESS] Stage 1: Basic Cleaning")
    print("Sample:", cleaned_basic[:200] + "..." if len(cleaned_basic) > 200 else cleaned_basic)
    print("Length:", len(cleaned_basic))
    
    # Step 3: Remove boilerplate
    document_text = remove_boilerplate(cleaned_basic)
    print("\n[PROCESS] Stage 2: Boilerplate Removal")
    print("Sample:", document_text[:200] + "..." if len(document_text) > 200 else document_text)
    print("Length:", len(document_text))
    
    # Step 5 & 6: Split into semantic chunks
    chunks = chunk_document(document_text, url, timestamp)
    print("\n[PROCESS] Stage 3: Semantic Chunking")
    if chunks:
        print("First chunk sample:", chunks[0]['text'][:200] + "..." if len(chunks[0]['text']) > 200 else chunks[0]['text'])
    print("Total chunks created:", len(chunks))
    
    # Step 7: Create Final Output Structure
    return {
        "title": title,
        "url": url,
        "timestamp": timestamp,
        "document_text": document_text,
        "chunks": chunks
    }
