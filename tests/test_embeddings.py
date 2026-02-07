"""Tests for embeddings module."""

import pytest
import numpy as np

from pdf_context_narrator.embeddings import (
    EmbeddingsProvider,
    SentenceTransformerEmbeddings,
    get_embeddings_provider,
)


@pytest.fixture(scope="module")
def embeddings_provider():
    """Create a SentenceTransformer embeddings provider for testing."""
    try:
        provider = SentenceTransformerEmbeddings(
            model_name="all-MiniLM-L6-v2",
            device="cpu",
        )
        return provider
    except Exception as e:
        pytest.skip(f"Could not load embeddings model: {e}")


def test_embeddings_provider_is_abstract():
    """Test that EmbeddingsProvider cannot be instantiated directly."""
    with pytest.raises(TypeError):
        EmbeddingsProvider()


def test_sentence_transformer_initialization():
    """Test SentenceTransformer embeddings initialization."""
    try:
        provider = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        assert provider is not None
        assert provider.model_name == "all-MiniLM-L6-v2"
    except Exception as e:
        pytest.skip(f"Could not load embeddings model: {e}")


def test_embed_single_text(embeddings_provider):
    """Test embedding a single text."""
    text = "This is a test sentence."
    embedding = embeddings_provider.embed_text(text)
    
    assert isinstance(embedding, np.ndarray)
    assert len(embedding.shape) == 1  # Should be 1D array
    assert embedding.shape[0] == embeddings_provider.get_dimension()


def test_embed_batch(embeddings_provider):
    """Test embedding multiple texts in a batch."""
    texts = [
        "First test sentence.",
        "Second test sentence.",
        "Third test sentence.",
    ]
    embeddings = embeddings_provider.embed_batch(texts)
    
    assert isinstance(embeddings, np.ndarray)
    assert len(embeddings.shape) == 2  # Should be 2D array
    assert embeddings.shape[0] == len(texts)
    assert embeddings.shape[1] == embeddings_provider.get_dimension()


def test_embed_empty_batch(embeddings_provider):
    """Test embedding an empty batch."""
    embeddings = embeddings_provider.embed_batch([])
    
    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape[0] == 0


def test_embedding_dimension(embeddings_provider):
    """Test that embedding dimension is consistent."""
    text1 = "Short text."
    text2 = "This is a much longer text with many more words to embed."
    
    embedding1 = embeddings_provider.embed_text(text1)
    embedding2 = embeddings_provider.embed_text(text2)
    
    assert embedding1.shape[0] == embedding2.shape[0]
    assert embedding1.shape[0] == embeddings_provider.get_dimension()


def test_embedding_similarity(embeddings_provider):
    """Test that similar texts have similar embeddings."""
    text1 = "The cat sat on the mat."
    text2 = "A cat is sitting on a mat."
    text3 = "Python is a programming language."
    
    emb1 = embeddings_provider.embed_text(text1)
    emb2 = embeddings_provider.embed_text(text2)
    emb3 = embeddings_provider.embed_text(text3)
    
    # Cosine similarity between embeddings
    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    sim_12 = cosine_similarity(emb1, emb2)
    sim_13 = cosine_similarity(emb1, emb3)
    
    # Similar texts should have higher similarity than dissimilar texts
    assert sim_12 > sim_13


def test_get_embeddings_provider_sentence_transformer():
    """Test factory function with sentence-transformer provider."""
    try:
        provider = get_embeddings_provider(
            provider="sentence-transformer",
            model_name="all-MiniLM-L6-v2",
        )
        
        assert isinstance(provider, SentenceTransformerEmbeddings)
        assert provider.model_name == "all-MiniLM-L6-v2"
    except Exception as e:
        pytest.skip(f"Could not load embeddings model: {e}")


def test_get_embeddings_provider_unknown():
    """Test factory function with unknown provider."""
    with pytest.raises(ValueError, match="Unknown embeddings provider"):
        get_embeddings_provider(provider="unknown-provider")


def test_batch_vs_single_embedding_consistency(embeddings_provider):
    """Test that batch and single embeddings are consistent."""
    text = "Test sentence for consistency check."
    
    # Get embedding via single method
    single_embedding = embeddings_provider.embed_text(text)
    
    # Get embedding via batch method
    batch_embeddings = embeddings_provider.embed_batch([text])
    
    # They should be very close (allowing for small numerical differences)
    np.testing.assert_allclose(single_embedding, batch_embeddings[0], rtol=1e-5)
