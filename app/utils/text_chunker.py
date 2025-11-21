from typing import List

class TextChunker:
    """Split text into chunks for processing"""
    
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: The text to chunk
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            # Calculate end position
            end = start + self.chunk_size
            
            # If this is not the last chunk, try to break at a sentence or word boundary
            if end < text_length:
                # Look for sentence boundaries (., !, ?) within the overlap region
                search_start = max(start, end - self.chunk_overlap)
                for delimiter in ['. ', '! ', '? ', '\n\n', '\n']:
                    delimiter_pos = text.rfind(delimiter, search_start, end)
                    if delimiter_pos != -1:
                        end = delimiter_pos + len(delimiter)
                        break
            
            # Extract chunk
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.chunk_overlap if end < text_length else text_length
        
        return chunks
