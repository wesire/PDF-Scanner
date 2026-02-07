"""Text chunking module for creating semantic chunks with overlap."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SourceReference:
    """Reference to the source of a text chunk."""
    
    file: str
    page: Optional[int] = None
    section: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "file": self.file,
            "page": self.page,
            "section": self.section,
        }


@dataclass
class TextChunk:
    """A chunk of text with metadata and source reference."""
    
    text: str
    source: SourceReference
    chunk_id: int
    start_char: int
    end_char: int
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "source": self.source.to_dict(),
            "chunk_id": self.chunk_id,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "metadata": self.metadata,
        }


class SemanticChunker:
    """
    Create semantic chunks from text with configurable size and overlap.
    
    Target chunk size: 800-1200 characters
    Overlap: 120 characters
    """
    
    def __init__(
        self,
        min_chunk_size: int = 800,
        max_chunk_size: int = 1200,
        overlap_size: int = 120,
    ):
        """
        Initialize the semantic chunker.
        
        Args:
            min_chunk_size: Minimum target chunk size in characters
            max_chunk_size: Maximum target chunk size in characters
            overlap_size: Number of overlapping characters between chunks
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
    
    def chunk_text(
        self,
        text: str,
        source: SourceReference,
        metadata: Optional[dict] = None,
    ) -> List[TextChunk]:
        """
        Chunk text into semantic chunks with overlap.
        
        Args:
            text: The text to chunk
            source: Source reference information
            metadata: Optional additional metadata
            
        Returns:
            List of TextChunk objects
        """
        if not text:
            return []
        
        chunks = []
        chunk_id = 0
        start_pos = 0
        
        while start_pos < len(text):
            # Calculate end position for this chunk
            end_pos = min(start_pos + self.max_chunk_size, len(text))
            
            # If we're not at the end, try to find a good break point
            if end_pos < len(text):
                end_pos = self._find_break_point(text, start_pos, end_pos)
            
            # Extract the chunk text
            chunk_text = text[start_pos:end_pos].strip()
            
            # Only create chunk if it meets minimum size or is the last chunk
            if len(chunk_text) >= self.min_chunk_size or end_pos >= len(text):
                chunk = TextChunk(
                    text=chunk_text,
                    source=source,
                    chunk_id=chunk_id,
                    start_char=start_pos,
                    end_char=end_pos,
                    metadata=metadata or {},
                )
                chunks.append(chunk)
                chunk_id += 1
            
            # Move start position forward, accounting for overlap
            if end_pos >= len(text):
                break
            
            # Calculate next start position with overlap
            next_start = end_pos - self.overlap_size
            
            # Ensure we make progress
            if next_start <= start_pos:
                next_start = end_pos
            
            start_pos = next_start
        
        return chunks
    
    def _find_break_point(self, text: str, start: int, end: int) -> int:
        """
        Find a good break point for the chunk.
        
        Prioritizes:
        1. Paragraph breaks (double newline)
        2. Sentence breaks (period, question mark, exclamation)
        3. Clause breaks (comma, semicolon, colon)
        4. Word boundaries (space)
        
        Args:
            text: The full text
            start: Start position of the chunk
            end: Desired end position of the chunk
            
        Returns:
            Adjusted end position
        """
        # Look for paragraph breaks (search backwards from end)
        search_text = text[start:end]
        para_idx = search_text.rfind('\n\n')
        if para_idx != -1 and para_idx > len(search_text) - 100:
            return start + para_idx + 2
        
        # Look for sentence breaks near the end
        sentence_breaks = ['. ', '? ', '! ', '.\n', '?\n', '!\n']
        for i in range(min(100, end - start)):
            pos = end - i
            if pos <= start:
                break
            for break_str in sentence_breaks:
                if text[pos:pos + len(break_str)] == break_str:
                    return pos + len(break_str)
        
        # Look for clause breaks
        clause_breaks = [', ', '; ', ': ', ',\n', ';\n', ':\n']
        for i in range(min(50, end - start)):
            pos = end - i
            if pos <= start:
                break
            for break_str in clause_breaks:
                if text[pos:pos + len(break_str)] == break_str:
                    return pos + len(break_str)
        
        # Fall back to word boundary
        for i in range(min(50, end - start)):
            pos = end - i
            if pos <= start:
                break
            if text[pos:pos + 1] == ' ':
                return pos + 1
        
        # If no good break point found, use the original end
        return end
