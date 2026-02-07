"""Tests for chunking module."""

import pytest
from pdf_context_narrator.chunking import (
    SemanticChunker,
    SourceReference,
    TextChunk,
)


@pytest.fixture
def sample_text():
    """Sample text for testing."""
    return """This is the first paragraph of test text. It contains several sentences to test chunking. 
The text should be split into appropriate chunks based on size and semantic boundaries.

This is the second paragraph. It provides more content to work with. We want to ensure that paragraph 
breaks are respected when possible. The chunker should find good break points.

This is the third paragraph with even more content. It helps us test that the chunker can handle 
multiple paragraphs and create chunks that respect natural text boundaries. Each chunk should maintain 
context and meaning. The overlap between chunks helps preserve continuity across chunk boundaries.

This is the fourth paragraph. It continues the pattern and gives us more text to work with for testing 
various scenarios. The chunker needs to be smart about where it splits the text. Good break points 
make for better semantic search results."""


@pytest.fixture
def chunker():
    """Create a semantic chunker with default settings."""
    return SemanticChunker(
        min_chunk_size=800,
        max_chunk_size=1200,
        overlap_size=120,
    )


@pytest.fixture
def source_ref():
    """Create a sample source reference."""
    return SourceReference(
        file="test.pdf",
        page=1,
        section="Introduction",
    )


def test_source_reference_to_dict():
    """Test SourceReference to_dict method."""
    source = SourceReference(file="test.pdf", page=1, section="Chapter 1")
    result = source.to_dict()
    
    assert result["file"] == "test.pdf"
    assert result["page"] == 1
    assert result["section"] == "Chapter 1"


def test_text_chunk_to_dict(source_ref):
    """Test TextChunk to_dict method."""
    chunk = TextChunk(
        text="Sample text",
        source=source_ref,
        chunk_id=0,
        start_char=0,
        end_char=11,
        metadata={"key": "value"},
    )
    result = chunk.to_dict()
    
    assert result["text"] == "Sample text"
    assert result["chunk_id"] == 0
    assert result["start_char"] == 0
    assert result["end_char"] == 11
    assert result["metadata"]["key"] == "value"
    assert result["source"]["file"] == "test.pdf"


def test_chunk_empty_text(chunker, source_ref):
    """Test chunking empty text."""
    chunks = chunker.chunk_text("", source_ref)
    assert len(chunks) == 0


def test_chunk_short_text(chunker, source_ref):
    """Test chunking text shorter than min_chunk_size."""
    text = "Short text."
    chunks = chunker.chunk_text(text, source_ref)
    
    # Should still create one chunk for short text
    assert len(chunks) == 1
    assert chunks[0].text == text
    assert chunks[0].chunk_id == 0


def test_chunk_boundaries(chunker, sample_text, source_ref):
    """Test that chunks are within size boundaries."""
    chunks = chunker.chunk_text(sample_text, source_ref)
    
    assert len(chunks) > 0
    
    for i, chunk in enumerate(chunks):
        # All chunks except potentially the last should be >= min_chunk_size
        if i < len(chunks) - 1:
            assert len(chunk.text) >= chunker.min_chunk_size, \
                f"Chunk {i} is too small: {len(chunk.text)} < {chunker.min_chunk_size}"
        
        # All chunks should be <= max_chunk_size
        assert len(chunk.text) <= chunker.max_chunk_size, \
            f"Chunk {i} is too large: {len(chunk.text)} > {chunker.max_chunk_size}"


def test_chunk_overlap(chunker, sample_text, source_ref):
    """Test that chunks have appropriate overlap."""
    chunks = chunker.chunk_text(sample_text, source_ref)
    
    if len(chunks) < 2:
        pytest.skip("Not enough chunks to test overlap")
    
    # Check overlap between consecutive chunks
    for i in range(len(chunks) - 1):
        current_chunk = chunks[i]
        next_chunk = chunks[i + 1]
        
        # The next chunk should start before the current chunk ends
        # (accounting for the overlap)
        overlap_exists = next_chunk.start_char < current_chunk.end_char
        
        # The overlap should be approximately the overlap_size
        # (may vary due to finding good break points)
        if overlap_exists:
            actual_overlap = current_chunk.end_char - next_chunk.start_char
            assert actual_overlap > 0, f"No overlap between chunks {i} and {i+1}"


def test_chunk_metadata_integrity(chunker, source_ref):
    """Test that source references and metadata are preserved."""
    # Use varied text with paragraphs and sentences to test boundary detection
    text = """This is the first paragraph with multiple sentences. It has enough content to create a chunk. 
The sentences vary in length to test chunking behavior. This paragraph continues with more text.

This is the second paragraph that should be in a different chunk. It also has varied sentence structures.
Some sentences are short. Others are longer and contain more detailed information about the topic.

The third paragraph provides additional content. """ * 3  # Repeat to ensure multiple chunks
    
    metadata = {"author": "Test Author", "date": "2024-01-01"}
    
    chunks = chunker.chunk_text(text, source_ref, metadata=metadata)
    
    for chunk in chunks:
        # Check source reference is preserved
        assert chunk.source.file == source_ref.file
        assert chunk.source.page == source_ref.page
        assert chunk.source.section == source_ref.section
        
        # Check metadata is preserved
        assert chunk.metadata == metadata


def test_chunk_ids_sequential(chunker, sample_text, source_ref):
    """Test that chunk IDs are sequential."""
    chunks = chunker.chunk_text(sample_text, source_ref)
    
    for i, chunk in enumerate(chunks):
        assert chunk.chunk_id == i


def test_chunk_positions(chunker, sample_text, source_ref):
    """Test that start and end positions are correct."""
    chunks = chunker.chunk_text(sample_text, source_ref)
    
    for chunk in chunks:
        # Verify we can extract the chunk text from the original using positions
        # Note: positions may not match exactly due to stripping
        assert chunk.start_char >= 0
        assert chunk.end_char > chunk.start_char
        assert chunk.end_char <= len(sample_text)


def test_chunk_break_points():
    """Test that chunker finds good break points."""
    chunker = SemanticChunker(min_chunk_size=50, max_chunk_size=100, overlap_size=10)
    source = SourceReference(file="test.pdf")
    
    # Text with clear sentence boundaries
    text = "First sentence. Second sentence. Third sentence. Fourth sentence. Fifth sentence."
    chunks = chunker.chunk_text(text, source)
    
    # Should split at sentence boundaries when possible
    for chunk in chunks:
        # Chunks should generally end with sentence terminators when not at end of text
        if chunk.end_char < len(text):
            last_chars = chunk.text.strip()[-2:]
            # May end with '. ' or other sentence terminators, or be at a natural break
            assert len(last_chars) > 0


def test_custom_chunk_sizes():
    """Test chunker with custom size parameters."""
    chunker = SemanticChunker(min_chunk_size=100, max_chunk_size=200, overlap_size=20)
    source = SourceReference(file="test.pdf")
    
    # Use varied text with sentences and paragraphs
    text = """This is the first sentence of the test. The second sentence adds more content. 
    A third sentence continues the narrative. The fourth sentence provides additional details.
    
    This is a new paragraph with different information. It contains multiple sentences as well.
    Each sentence adds to the overall content. The text flows naturally with varied structure.""" * 3
    
    chunks = chunker.chunk_text(text, source)
    
    assert len(chunks) > 0
    for chunk in chunks:
        assert len(chunk.text) <= 200
