import re
import hashlib
from typing import Set
from datetime import datetime

def normalize_text(text: str) -> str:
    """Strip whitespace, collapse multiple spaces, and remove basic noise."""
    if not text:
        return ""
    # Collapse multiple spaces/newlines
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def get_event_fingerprint(source: str, item_id: str, author: str, text: str) -> str:
    """Generate a unique fingerprint for deduplication."""
    # Use first 50 chars of normalized text for prefix-based dedupe
    text_prefix = normalize_text(text)[:50]
    raw_str = f"{source}:{item_id}:{author}:{text_prefix}"
    return hashlib.md5(raw_str.encode()).hexdigest()

class Deduplicator:
    def __init__(self, cache_size: int = 1000):
        self.seen_fingerprints: Set[str] = set()
        self.cache_size = cache_size

    def is_duplicate(self, source: str, item_id: str, author: str, text: str) -> bool:
        fingerprint = get_event_fingerprint(source, item_id, author, text)
        if fingerprint in self.seen_fingerprints:
            return True
        
        # Basic LRU-ish cleanup if cache grows too large
        if len(self.seen_fingerprints) >= self.cache_size:
            self.seen_fingerprints.clear() # Simple clear for now
            
        self.seen_fingerprints.add(fingerprint)
        return False
