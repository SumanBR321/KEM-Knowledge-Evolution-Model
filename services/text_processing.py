import re
from typing import Dict, Any, List
from bs4 import BeautifulSoup, Comment
from langchain_text_splitters import RecursiveCharacterTextSplitter

def extract_main_content(html_content: str, title: str) -> Dict[str, Any]:
    """
    Advanced research-based text cleaning pipeline (TTR, ATTR, TKD).
    """
    if not html_content:
        return {"clean_text": "", "word_count": 0}

    soup = BeautifulSoup(html_content, 'lxml')

    # --- Step 1: Remove Useless HTML Elements ---
    useless_tags = [
        'script', 'style', 'noscript', 'svg', 'canvas', 'iframe', 
        'footer', 'nav', 'form', 'aside', 'header'
    ]
    for tag in soup.find_all(useless_tags):
        tag.decompose()

    # Remove comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Remove hidden elements (naive check for style="display:none")
    for hidden in soup.find_all(style=re.compile(r'display:\s*none', re.I)):
        hidden.decompose()

    # --- Step 2 & 3: Extract & Score Blocks ---
    # Keywords from title for TKD
    title_keywords = set(re.findall(r'\w+', title.lower()))
    
    blocks = []
    # Segment into potential content blocks
    potential_tags = ['p', 'div', 'article', 'section', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    
    for element in soup.find_all(potential_tags):
        # Avoid nested scoring: if a block is mostly contained within another already processed block, skip?
        # For simplicity in real-time, we'll process all and merge later.
        
        text = element.get_text(separator=' ', strip=True)
        if not text:
            continue
            
        # Features
        html_str = str(element)
        tag_count = len(re.findall(r'<[^>]+>', html_str))
        text_length = len(text)
        
        # 1. Text Density
        text_density = text_length / tag_count if tag_count > 0 else text_length
        
        # 2. Link Density
        links = element.find_all('a')
        link_text_length = sum(len(a.get_text(strip=True)) for a in links)
        link_density = link_text_length / text_length if text_length > 0 else 0
        
        # 3. Title Keyword Density
        block_words = re.findall(r'\w+', text.lower())
        tk_count = sum(1 for w in block_words if w in title_keywords)
        tk_density = tk_count # Score based on frequency
        
        # --- Step 4: Threshold Rules ---
        # Research thresholds: TD > 30, LD < 0.2, TKD >= 1
        if text_density > 25 and link_density < 0.3:
            # We are slightly more lenient than the user suggested for variety
            # But we check the TKD as a boost
            score = text_density * (1 - link_density)
            if tk_count > 0:
                score *= 1.5
                
            blocks.append({
                "text": text,
                "score": score,
                "tk_count": tk_count
            })

    # --- Step 5: Merge & Filter ---
    # Sort blocks by a heuristic or just keep order? Original order is better for reconstruction.
    # However, we only want "Valid" blocks.
    
    # Filter short fragments and duplicates
    unique_text = set()
    valid_text_segments = []
    
    for b in blocks:
        clean_s = b['text']
        # Word count check (> 30 words is ideal, but let's be realistic for headers etc)
        word_count = len(clean_s.split())
        
        if word_count < 10: # More lenient for semantic flow
            continue
            
        if clean_s in unique_text:
            continue
            
        unique_text.add(clean_s)
        valid_text_segments.append(clean_s)

    # --- Step 6: Post-Processing ---
    combined_text = "\n\n".join(valid_text_segments)
    
    # Repeated whitespace
    combined_text = re.sub(r' +', ' ', combined_text)
    combined_text = re.sub(r'\n{3,}', '\n\n', combined_text)
    
    final_word_count = len(combined_text.split())
    
    return {
        "clean_text": combined_text.strip(),
        "word_count": final_word_count
    }

def chunk_document(document_text: str, source_url: str, timestamp: str) -> List[Dict[str, str]]:
    """
    Split document-level text into semantic chunks.
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
    html_content = data.get('content', '')
    title = data.get('title', '')
    url = data.get('url', '')
    timestamp = data.get('timestamp', '')
    
    print(f"\n[PROCESS] Received HTML content length: {len(html_content)}")
    
    # Advanced Pipeline v2
    extraction_result = extract_main_content(html_content, title)
    clean_text = extraction_result['clean_text']
    word_count = extraction_result['word_count']
    
    print(f"[PROCESS] Pipeline Result: {word_count} words extracted.")
    
    # Split into semantic chunks
    chunks = chunk_document(clean_text, url, timestamp)
    print(f"[PROCESS] Created {len(chunks)} chunks.")
    
    return {
        "title": title,
        "url": url,
        "timestamp": timestamp,
        "document_text": clean_text,
        "word_count": word_count,
        "chunks": chunks
    }
