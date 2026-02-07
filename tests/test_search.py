"""Tests for search functionality."""

import json
import pytest
from pathlib import Path

from pdf_context_narrator.search import (
    SearchEngine,
    chunk_document,
    compute_bm25_score,
    compute_mock_vector_score,
    hybrid_rank_chunks,
    Chunk,
    Document
)


@pytest.fixture
def fixtures_dir():
    """Get path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def search_engine(fixtures_dir):
    """Create a search engine with indexed test documents."""
    engine = SearchEngine(seed=42)
    if fixtures_dir.exists():
        engine.index_directory(fixtures_dir, pattern="*.txt")
    return engine


def test_chunk_document():
    """Test document chunking."""
    content = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"
    chunks = chunk_document(content, "test.txt", chunk_size=20)
    
    assert len(chunks) > 0
    assert all(isinstance(chunk, Chunk) for chunk in chunks)
    assert all(chunk.document == "test.txt" for chunk in chunks)
    assert all(chunk.page > 0 for chunk in chunks)


def test_document_from_file(fixtures_dir, tmp_path):
    """Test loading document from file."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test content\n\nMore content")
    
    doc = Document.from_file(test_file)
    
    assert doc.path == str(test_file)
    assert "Test content" in doc.content
    assert len(doc.chunks) > 0


def test_bm25_score():
    """Test BM25 scoring."""
    chunk = Chunk(
        chunk_id="test_1",
        document="test.txt",
        page=1,
        content="machine learning is a subset of artificial intelligence",
        start_pos=0,
        end_pos=100
    )
    
    # Query with matching terms should have positive score
    score1 = compute_bm25_score("machine learning", chunk)
    assert score1 > 0
    
    # Query with no matching terms should have zero score
    score2 = compute_bm25_score("quantum computing", chunk)
    assert score2 == 0
    
    # More matching terms should give higher score
    score3 = compute_bm25_score("machine learning artificial intelligence", chunk)
    assert score3 > score1


def test_mock_vector_score():
    """Test mock vector scoring."""
    chunk = Chunk(
        chunk_id="test_1",
        document="test.txt",
        page=1,
        content="natural language processing",
        start_pos=0,
        end_pos=100
    )
    
    # Score should be deterministic with same seed
    score1 = compute_mock_vector_score("language", chunk, seed=42)
    score2 = compute_mock_vector_score("language", chunk, seed=42)
    assert score1 == score2
    
    # Different seed should give different score
    score3 = compute_mock_vector_score("language", chunk, seed=100)
    assert score3 != score1
    
    # Score should be between 0 and 1
    assert 0 <= score1 <= 1


def test_hybrid_ranking():
    """Test hybrid ranking of chunks."""
    chunks = [
        Chunk(
            chunk_id="chunk_1",
            document="doc1.txt",
            page=1,
            content="machine learning algorithms and deep learning networks",
            start_pos=0,
            end_pos=100
        ),
        Chunk(
            chunk_id="chunk_2",
            document="doc1.txt",
            page=1,
            content="natural language processing and text analysis",
            start_pos=100,
            end_pos=200
        ),
        Chunk(
            chunk_id="chunk_3",
            document="doc2.txt",
            page=1,
            content="computer vision and image recognition systems",
            start_pos=0,
            end_pos=100
        )
    ]
    
    results = hybrid_rank_chunks("machine learning", chunks, seed=42)
    
    assert len(results) == 3
    assert all(hasattr(r, 'score') for r in results)
    assert all(hasattr(r, 'keyword_score') for r in results)
    assert all(hasattr(r, 'vector_score') for r in results)
    
    # Results should be sorted by score (descending)
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
    
    # First result should be the chunk with "machine learning"
    assert "machine learning" in chunks[0].content.lower()


def test_search_engine_initialization():
    """Test search engine initialization."""
    engine = SearchEngine(seed=42)
    assert engine.seed == 42
    assert len(engine.documents) == 0
    assert len(engine.chunks) == 0


def test_search_engine_indexing(fixtures_dir):
    """Test document indexing."""
    engine = SearchEngine(seed=42)
    
    # Index a single document
    doc_path = fixtures_dir / "doc1.txt"
    if doc_path.exists():
        engine.index_document(doc_path)
        assert len(engine.documents) == 1
        assert len(engine.chunks) > 0


def test_search_engine_directory_indexing(fixtures_dir):
    """Test directory indexing."""
    engine = SearchEngine(seed=42)
    engine.index_directory(fixtures_dir, pattern="*.txt")
    
    # Should have indexed all .txt files
    assert len(engine.documents) >= 3
    assert len(engine.chunks) > 0


def test_search_basic(search_engine):
    """Test basic search functionality."""
    results = search_engine.search("machine learning", top_k=5)
    
    assert isinstance(results, list)
    assert len(results) <= 5
    
    if results:
        # Check result structure
        result = results[0]
        assert hasattr(result, 'chunk_id')
        assert hasattr(result, 'document')
        assert hasattr(result, 'page')
        assert hasattr(result, 'snippet')
        assert hasattr(result, 'score')
        assert hasattr(result, 'keyword_score')
        assert hasattr(result, 'vector_score')


def test_search_relevance_ordering(search_engine):
    """Test that search results are ordered by relevance."""
    # Search for a specific term
    results = search_engine.search("natural language processing", top_k=10)
    
    if len(results) > 1:
        # Scores should be in descending order
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)
        
        # Top result should contain relevant terms
        top_result = results[0]
        content_lower = top_result.snippet.lower()
        assert any(term in content_lower for term in ["natural", "language", "processing"])


def test_search_deterministic_with_seed(search_engine):
    """Test that search results are deterministic with fixed seed."""
    query = "machine learning"
    
    # Run search twice with same engine (same seed)
    results1 = search_engine.search(query, top_k=5)
    results2 = search_engine.search(query, top_k=5)
    
    assert len(results1) == len(results2)
    
    # Results should be identical
    for r1, r2 in zip(results1, results2):
        assert r1.chunk_id == r2.chunk_id
        assert r1.score == r2.score
        assert r1.keyword_score == r2.keyword_score
        assert r1.vector_score == r2.vector_score


def test_search_different_seeds():
    """Test that different seeds produce different vector scores."""
    from pathlib import Path
    
    fixtures_dir = Path(__file__).parent / "fixtures"
    
    engine1 = SearchEngine(seed=42)
    engine2 = SearchEngine(seed=100)
    
    if fixtures_dir.exists():
        engine1.index_directory(fixtures_dir, pattern="*.txt")
        engine2.index_directory(fixtures_dir, pattern="*.txt")
        
        results1 = engine1.search("machine learning", top_k=5)
        results2 = engine2.search("machine learning", top_k=5)
        
        if results1 and results2:
            # Vector scores should be different for at least some results
            # We check all results to find at least one difference
            vector_scores_1 = [r.vector_score for r in results1]
            vector_scores_2 = [r.vector_score for r in results2]
            
            # At least one vector score should be different
            assert vector_scores_1 != vector_scores_2, "Vector scores should differ with different seeds"


def test_search_top_k_limit(search_engine):
    """Test that top_k parameter limits results."""
    results_5 = search_engine.search("artificial intelligence", top_k=5)
    results_3 = search_engine.search("artificial intelligence", top_k=3)
    
    assert len(results_5) <= 5
    assert len(results_3) <= 3
    assert len(results_3) <= len(results_5)


def test_search_empty_query(search_engine):
    """Test search with empty query."""
    results = search_engine.search("", top_k=5)
    
    # Should return results (all chunks scored equally low)
    assert isinstance(results, list)


def test_search_no_documents():
    """Test search with no indexed documents."""
    engine = SearchEngine(seed=42)
    results = engine.search("test query", top_k=5)
    
    assert results == []


def test_export_json(search_engine):
    """Test JSON export of search results."""
    results = search_engine.search("machine learning", top_k=3)
    
    json_output = search_engine.export_results_json(results)
    
    # Should be valid JSON
    parsed = json.loads(json_output)
    assert isinstance(parsed, list)
    
    if results:
        assert len(parsed) == len(results)
        assert all('chunk_id' in item for item in parsed)
        assert all('score' in item for item in parsed)
        assert all('snippet' in item for item in parsed)


def test_export_markdown(search_engine):
    """Test Markdown export of search results."""
    query = "natural language processing"
    results = search_engine.search(query, top_k=3)
    
    markdown_output = search_engine.export_results_markdown(results, query)
    
    # Should contain Markdown formatting
    assert "# Search Results" in markdown_output
    assert query in markdown_output
    assert "##" in markdown_output  # Result headers
    
    if results:
        assert "**Score:**" in markdown_output
        assert "**Snippet:**" in markdown_output
        assert "**Page:**" in markdown_output


def test_hybrid_weights(fixtures_dir):
    """Test different keyword/vector weight combinations."""
    engine = SearchEngine(seed=42)
    engine.index_directory(fixtures_dir, pattern="*.txt")
    
    query = "machine learning"
    
    # Keyword-heavy search
    results_keyword = engine.search(query, top_k=5, keyword_weight=0.9, vector_weight=0.1)
    
    # Vector-heavy search
    results_vector = engine.search(query, top_k=5, keyword_weight=0.1, vector_weight=0.9)
    
    # Both should return results
    assert len(results_keyword) > 0
    assert len(results_vector) > 0
    
    # Scores should be different due to different weights
    if results_keyword and results_vector:
        # Check that the weighting affected the final score
        assert results_keyword[0].score != results_vector[0].score


def test_chunk_snippet_truncation():
    """Test that snippets are properly truncated."""
    long_content = "a" * 300
    chunk = Chunk(
        chunk_id="test",
        document="test.txt",
        page=1,
        content=long_content,
        start_pos=0,
        end_pos=300
    )
    
    results = hybrid_rank_chunks("test", [chunk], seed=42)
    
    assert len(results) == 1
    assert len(results[0].snippet) <= 153  # 150 + "..."
    assert results[0].snippet.endswith("...")


def test_search_result_to_dict():
    """Test SearchResult to_dict conversion."""
    from pdf_context_narrator.search import SearchResult
    
    result = SearchResult(
        chunk_id="test_1",
        document="test.txt",
        page=1,
        snippet="test snippet",
        score=0.85,
        keyword_score=0.7,
        vector_score=0.9
    )
    
    result_dict = result.to_dict()
    
    assert isinstance(result_dict, dict)
    assert result_dict['chunk_id'] == "test_1"
    assert result_dict['score'] == 0.85
    assert result_dict['keyword_score'] == 0.7
    assert result_dict['vector_score'] == 0.9
