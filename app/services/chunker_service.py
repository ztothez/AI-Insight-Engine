import re

def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    # Function logic: create overlapping sections so context is not lost at boundaries.
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks
