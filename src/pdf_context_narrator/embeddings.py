"""Embeddings abstraction for generating vector representations of text."""

from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np
from pathlib import Path

from pdf_context_narrator.logger import get_logger

logger = get_logger(__name__)


class EmbeddingsProvider(ABC):
    """Abstract base class for embeddings providers."""
    
    @abstractmethod
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding vector for a single text.
        
        Args:
            text: The text to embed
            
        Returns:
            Numpy array containing the embedding vector
        """
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embedding vectors for a batch of texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Numpy array with shape (n_texts, embedding_dim)
        """
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors.
        
        Returns:
            The embedding dimension
        """
        pass


class SentenceTransformerEmbeddings(EmbeddingsProvider):
    """Embeddings provider using Sentence Transformers."""
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: Optional[str] = None,
        cache_dir: Optional[Path] = None,
    ):
        """
        Initialize Sentence Transformer embeddings.
        
        Args:
            model_name: Name of the sentence transformer model
            device: Device to use ('cpu', 'cuda', or None for auto)
            cache_dir: Directory to cache the model
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers is required for SentenceTransformerEmbeddings. "
                "Install it with: pip install sentence-transformers"
            )
        
        self.model_name = model_name
        self.device = device
        self.cache_dir = str(cache_dir) if cache_dir else None
        
        logger.info(f"Loading sentence transformer model: {model_name}")
        self.model = SentenceTransformer(
            model_name,
            device=device,
            cache_folder=self.cache_dir,
        )
        logger.info(f"Model loaded successfully. Dimension: {self.get_dimension()}")
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding vector for a single text.
        
        Args:
            text: The text to embed
            
        Returns:
            Numpy array containing the embedding vector
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embedding vectors for a batch of texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Numpy array with shape (n_texts, embedding_dim)
        """
        if not texts:
            return np.array([])
        
        logger.debug(f"Embedding batch of {len(texts)} texts")
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 100,
        )
        return embeddings
    
    def get_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors.
        
        Returns:
            The embedding dimension
        """
        return self.model.get_sentence_embedding_dimension()


def get_embeddings_provider(
    provider: str = "sentence-transformer",
    model_name: str = "all-MiniLM-L6-v2",
    **kwargs,
) -> EmbeddingsProvider:
    """
    Factory function to get an embeddings provider.
    
    Args:
        provider: Name of the provider ('sentence-transformer')
        model_name: Name of the model to use
        **kwargs: Additional arguments for the provider
        
    Returns:
        An instance of EmbeddingsProvider
    """
    if provider == "sentence-transformer":
        return SentenceTransformerEmbeddings(model_name=model_name, **kwargs)
    else:
        raise ValueError(f"Unknown embeddings provider: {provider}")
