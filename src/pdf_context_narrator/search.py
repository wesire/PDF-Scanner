"""Search functionality for PDF Context Narrator."""

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any
import hashlib


@dataclass
class SearchResult:
    """A single search result."""
    
    chunk_id: str
    document: str
    page: int
    snippet: str
    score: float
    keyword_score: float
    vector_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Document:
    """A document with content and metadata."""
    
    path: str
    content: str
    chunks: List['Chunk']
    
    @staticmethod
    def from_file(path: Path) -> 'Document':
        """Load a document from a file."""
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        chunks = chunk_document(content, str(path))
        return Document(
            path=str(path),
            content=content,
            chunks=chunks
        )


@dataclass
class Chunk:
    """A chunk of text from a document."""
    
    chunk_id: str
    document: str
    page: int
    content: str
    start_pos: int
    end_pos: int
    embedding: Optional[List[float]] = None


def chunk_document(content: str, document_path: str, chunk_size: int = 500) -> List[Chunk]:
    """
    Split document into chunks for search.
    
    Args:
        content: Document content
        document_path: Path to the document
        chunk_size: Size of each chunk in characters
    
    Returns:
        List of chunks
    """
    chunks = []
    
    # Split by paragraphs first
    paragraphs = content.split('\n\n')
    
    current_chunk = ""
    current_pos = 0
    chunk_idx = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # If adding this paragraph exceeds chunk size, save current chunk
        if current_chunk and len(current_chunk) + len(para) > chunk_size:
            chunk_id = f"{Path(document_path).stem}_chunk_{chunk_idx}"
            # Estimate page number (assuming ~2000 chars per page)
            page = (current_pos // 2000) + 1
            
            chunks.append(Chunk(
                chunk_id=chunk_id,
                document=document_path,
                page=page,
                content=current_chunk.strip(),
                start_pos=current_pos,
                end_pos=current_pos + len(current_chunk)
            ))
            
            chunk_idx += 1
            current_chunk = para
            current_pos += len(current_chunk) + 2  # +2 for \n\n
        else:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
    
    # Add the last chunk
    if current_chunk:
        chunk_id = f"{Path(document_path).stem}_chunk_{chunk_idx}"
        page = (current_pos // 2000) + 1
        chunks.append(Chunk(
            chunk_id=chunk_id,
            document=document_path,
            page=page,
            content=current_chunk.strip(),
            start_pos=current_pos,
            end_pos=current_pos + len(current_chunk)
        ))
    
    return chunks


def compute_bm25_score(query: str, chunk: Chunk, avg_doc_length: float = 500.0) -> float:
    """
    Compute BM25-like keyword score for a chunk.
    
    Args:
        query: Search query
        chunk: Text chunk to score
        avg_doc_length: Average document length for normalization
    
    Returns:
        BM25 score
    """
    # BM25 parameters
    k1 = 1.5
    b = 0.75
    
    # Tokenize query and chunk
    query_terms = set(query.lower().split())
    chunk_text = chunk.content.lower()
    chunk_terms = chunk_text.split()
    
    # Calculate term frequencies
    score = 0.0
    doc_length = len(chunk_terms)
    
    for term in query_terms:
        tf = chunk_terms.count(term)
        if tf == 0:
            continue
        
        # BM25 formula (simplified without IDF since we don't have corpus stats)
        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * (doc_length / avg_doc_length))
        score += numerator / denominator
    
    return score


def compute_mock_vector_score(query: str, chunk: Chunk, seed: int = 42) -> float:
    """
    Compute mock vector similarity score using deterministic hash-based method.
    
    Args:
        query: Search query
        chunk: Text chunk to score
        seed: Random seed for deterministic output
    
    Returns:
        Mock vector similarity score (0-1)
    """
    # Create deterministic "embeddings" using hash
    query_hash = hashlib.md5(f"{seed}:{query}".encode()).hexdigest()
    chunk_hash = hashlib.md5(f"{seed}:{chunk.content[:100]}".encode()).hexdigest()
    
    # Convert hashes to pseudo-similarity score
    # Count matching characters in the hashes (simple overlap)
    matches = sum(1 for a, b in zip(query_hash, chunk_hash) if a == b)
    similarity = matches / len(query_hash)
    
    # Boost score if query terms appear in chunk
    query_terms = set(query.lower().split())
    chunk_text = chunk.content.lower()
    term_overlap = sum(1 for term in query_terms if term in chunk_text)
    
    if term_overlap > 0:
        similarity = min(1.0, similarity + (term_overlap * 0.15))
    
    return similarity


def hybrid_rank_chunks(
    query: str,
    chunks: List[Chunk],
    keyword_weight: float = 0.6,
    vector_weight: float = 0.4,
    seed: int = 42
) -> List[SearchResult]:
    """
    Rank chunks using hybrid keyword + vector scoring.
    
    Args:
        query: Search query
        chunks: List of chunks to rank
        keyword_weight: Weight for keyword score
        vector_weight: Weight for vector score
        seed: Random seed for deterministic vector scores
    
    Returns:
        Sorted list of search results
    """
    results = []
    avg_length = sum(len(c.content.split()) for c in chunks) / len(chunks) if chunks else 500
    
    for chunk in chunks:
        keyword_score = compute_bm25_score(query, chunk, avg_length)
        vector_score = compute_mock_vector_score(query, chunk, seed)
        
        # Normalize keyword score (rough normalization)
        keyword_score_normalized = min(1.0, keyword_score / 5.0)
        
        # Compute hybrid score
        hybrid_score = (keyword_weight * keyword_score_normalized + 
                       vector_weight * vector_score)
        
        # Create snippet (first 150 chars of chunk)
        snippet = chunk.content[:150]
        if len(chunk.content) > 150:
            snippet += "..."
        
        results.append(SearchResult(
            chunk_id=chunk.chunk_id,
            document=chunk.document,
            page=chunk.page,
            snippet=snippet,
            score=hybrid_score,
            keyword_score=keyword_score_normalized,
            vector_score=vector_score
        ))
    
    # Sort by score (descending)
    results.sort(key=lambda x: x.score, reverse=True)
    
    return results


class SearchEngine:
    """Search engine for document retrieval."""
    
    def __init__(self, seed: int = 42):
        """
        Initialize search engine.
        
        Args:
            seed: Random seed for deterministic results
        """
        self.documents: List[Document] = []
        self.chunks: List[Chunk] = []
        self.seed = seed
    
    def index_document(self, path: Path) -> None:
        """
        Index a document for search.
        
        Args:
            path: Path to document file
        """
        doc = Document.from_file(path)
        self.documents.append(doc)
        self.chunks.extend(doc.chunks)
    
    def index_directory(self, directory: Path, pattern: str = "*.txt") -> None:
        """
        Index all documents in a directory.
        
        Args:
            directory: Directory containing documents
            pattern: File pattern to match
        """
        for path in directory.glob(pattern):
            if path.is_file():
                self.index_document(path)
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        keyword_weight: float = 0.6,
        vector_weight: float = 0.4
    ) -> List[SearchResult]:
        """
        Search indexed documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
            keyword_weight: Weight for keyword scoring
            vector_weight: Weight for vector scoring
        
        Returns:
            List of top search results
        """
        if not self.chunks:
            return []
        
        results = hybrid_rank_chunks(
            query=query,
            chunks=self.chunks,
            keyword_weight=keyword_weight,
            vector_weight=vector_weight,
            seed=self.seed
        )
        
        return results[:top_k]
    
    def export_results_json(self, results: List[SearchResult]) -> str:
        """
        Export search results as JSON.
        
        Args:
            results: Search results to export
        
        Returns:
            JSON string
        """
        return json.dumps([r.to_dict() for r in results], indent=2)
    
    def export_results_markdown(self, results: List[SearchResult], query: str) -> str:
        """
        Export search results as Markdown.
        
        Args:
            results: Search results to export
            query: Original search query
        
        Returns:
            Markdown string
        """
        lines = [
            f"# Search Results for: {query}",
            "",
            f"Found {len(results)} results",
            ""
        ]
        
        for i, result in enumerate(results, 1):
            lines.extend([
                f"## Result {i}",
                "",
                f"**Document:** {Path(result.document).name}",
                f"**Page:** {result.page}",
                f"**Score:** {result.score:.4f} (keyword: {result.keyword_score:.4f}, vector: {result.vector_score:.4f})",
                "",
                f"**Snippet:**",
                f"> {result.snippet}",
                "",
                "---",
                ""
            ])
        
        return "\n".join(lines)
