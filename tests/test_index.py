"""Tests for FAISS index module."""

import pytest
import json
from pathlib import Path
import numpy as np

from pdf_context_narrator.index import FAISSIndexManager
from pdf_context_narrator.embeddings import get_embeddings_provider
from pdf_context_narrator.chunking import TextChunk, SourceReference


@pytest.fixture(scope="module")
def embeddings_provider():
    """Create embeddings provider for testing."""
    try:
        return get_embeddings_provider(
            provider="sentence-transformer",
            model_name="all-MiniLM-L6-v2",
        )
    except Exception as e:
        pytest.skip(f"Could not load embeddings model: {e}")


@pytest.fixture
def index_manager(embeddings_provider):
    """Create FAISS index manager for testing."""
    return FAISSIndexManager(embeddings_provider=embeddings_provider)


@pytest.fixture
def sample_chunks():
    """Create sample text chunks for testing."""
    source = SourceReference(file="test.pdf", page=1, section="Introduction")
    
    chunks = [
        TextChunk(
            text="Python is a high-level programming language.",
            source=source,
            chunk_id=0,
            start_char=0,
            end_char=45,
            metadata={"author": "Test"},
        ),
        TextChunk(
            text="Machine learning is a subset of artificial intelligence.",
            source=source,
            chunk_id=1,
            start_char=45,
            end_char=102,
            metadata={"author": "Test"},
        ),
        TextChunk(
            text="Data science involves analyzing and interpreting complex data.",
            source=source,
            chunk_id=2,
            start_char=102,
            end_char=165,
            metadata={"author": "Test"},
        ),
    ]
    return chunks


def test_index_initialization(index_manager):
    """Test that index manager initializes correctly."""
    assert index_manager is not None
    assert index_manager.index is not None
    assert index_manager.dimension > 0
    assert index_manager.index.ntotal == 0  # Empty initially


def test_add_chunks(index_manager, sample_chunks):
    """Test adding chunks to the index."""
    index_manager.add_chunks(sample_chunks)
    
    assert index_manager.index.ntotal == len(sample_chunks)
    assert len(index_manager.metadata) == len(sample_chunks)


def test_add_empty_chunks(index_manager):
    """Test adding empty list of chunks."""
    initial_count = index_manager.index.ntotal
    index_manager.add_chunks([])
    
    assert index_manager.index.ntotal == initial_count


def test_search_empty_index(index_manager):
    """Test searching in an empty index."""
    results = index_manager.search("Python programming", k=5)
    assert len(results) == 0


def test_search_with_results(index_manager, sample_chunks):
    """Test searching with results."""
    index_manager.add_chunks(sample_chunks)
    
    # Search for something related to first chunk
    results = index_manager.search("Python programming language", k=3)
    
    assert len(results) > 0
    assert len(results) <= 3
    
    # Each result should be a tuple of (metadata, distance)
    for metadata, distance in results:
        assert isinstance(metadata, dict)
        assert isinstance(distance, float)
        assert "text" in metadata
        assert "source" in metadata


def test_search_relevance(index_manager, sample_chunks):
    """Test that search returns relevant results."""
    index_manager.add_chunks(sample_chunks)
    
    # Search for Python-related content
    results = index_manager.search("Python", k=3)
    
    # First result should be the Python chunk
    top_result = results[0]
    assert "Python" in top_result[0]["text"]


def test_metadata_preservation(index_manager, sample_chunks):
    """Test that metadata is preserved correctly."""
    index_manager.add_chunks(sample_chunks)
    
    for i, chunk in enumerate(sample_chunks):
        metadata = index_manager.metadata[i]
        
        assert metadata["text"] == chunk.text
        assert metadata["chunk_id"] == chunk.chunk_id
        assert metadata["start_char"] == chunk.start_char
        assert metadata["end_char"] == chunk.end_char
        assert metadata["source"]["file"] == chunk.source.file
        assert metadata["source"]["page"] == chunk.source.page
        assert metadata["metadata"]["author"] == "Test"


def test_save_and_load(index_manager, sample_chunks, tmp_path):
    """Test saving and loading index."""
    index_path = tmp_path / "test_index"
    index_manager.index_path = index_path
    
    # Add chunks and save
    index_manager.add_chunks(sample_chunks)
    index_manager.save()
    
    # Verify files exist
    assert index_path.with_suffix(".faiss").exists()
    assert index_path.with_suffix(".meta.json").exists()
    
    # Create new index manager and load
    new_manager = FAISSIndexManager(
        embeddings_provider=index_manager.embeddings_provider,
        index_path=index_path,
    )
    new_manager.load()
    
    # Verify loaded data
    assert new_manager.index.ntotal == len(sample_chunks)
    assert len(new_manager.metadata) == len(sample_chunks)
    
    # Verify metadata matches
    for i, chunk in enumerate(sample_chunks):
        assert new_manager.metadata[i]["text"] == chunk.text


def test_save_without_path(index_manager):
    """Test that saving without path raises error."""
    with pytest.raises(ValueError, match="No path specified"):
        index_manager.save()


def test_load_without_path(index_manager):
    """Test that loading without path raises error."""
    with pytest.raises(ValueError, match="No path specified"):
        index_manager.load()


def test_load_nonexistent_file(index_manager, tmp_path):
    """Test loading from non-existent file."""
    index_path = tmp_path / "nonexistent_index"
    
    with pytest.raises(FileNotFoundError):
        index_manager.load(index_path)


def test_update_index(index_manager, sample_chunks):
    """Test updating index with new chunks."""
    # Add initial chunks
    initial_chunks = sample_chunks[:2]
    index_manager.add_chunks(initial_chunks)
    initial_count = index_manager.index.ntotal
    
    # Update with more chunks
    new_chunks = sample_chunks[2:]
    index_manager.update(new_chunks)
    
    # Verify counts
    assert index_manager.index.ntotal == initial_count + len(new_chunks)
    assert len(index_manager.metadata) == len(sample_chunks)


def test_rebuild_index(index_manager, sample_chunks):
    """Test rebuilding index from scratch."""
    # Add some chunks
    index_manager.add_chunks(sample_chunks[:2])
    
    # Rebuild with different chunks
    new_chunks = sample_chunks[1:]
    index_manager.rebuild(new_chunks)
    
    # Verify index was rebuilt
    assert index_manager.index.ntotal == len(new_chunks)
    assert len(index_manager.metadata) == len(new_chunks)


def test_get_stats(index_manager, sample_chunks):
    """Test getting index statistics."""
    index_manager.add_chunks(sample_chunks)
    
    stats = index_manager.get_stats()
    
    assert stats["total_vectors"] == len(sample_chunks)
    assert stats["dimension"] == index_manager.dimension
    assert stats["metadata_count"] == len(sample_chunks)


def test_search_k_limit(index_manager, sample_chunks):
    """Test that search respects k parameter."""
    index_manager.add_chunks(sample_chunks)
    
    # Request more results than available
    results = index_manager.search("test", k=10)
    
    # Should return at most the number of chunks in index
    assert len(results) <= len(sample_chunks)


def test_metadata_format(tmp_path, index_manager, sample_chunks):
    """Test that saved metadata is valid JSON."""
    index_path = tmp_path / "test_index"
    index_manager.index_path = index_path
    
    index_manager.add_chunks(sample_chunks)
    index_manager.save()
    
    # Load and verify JSON format
    metadata_file = index_path.with_suffix(".meta.json")
    with open(metadata_file, "r") as f:
        metadata = json.load(f)
    
    assert isinstance(metadata, list)
    assert len(metadata) == len(sample_chunks)
    
    for item in metadata:
        assert "text" in item
        assert "source" in item
        assert "chunk_id" in item
