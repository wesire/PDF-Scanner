"""FAISS index manager for vector search with metadata storage."""

import json
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import numpy as np

from pdf_context_narrator.logger import get_logger
from pdf_context_narrator.chunking import TextChunk
from pdf_context_narrator.embeddings import EmbeddingsProvider

logger = get_logger(__name__)


class FAISSIndexManager:
    """
    Manager for FAISS vector index with metadata storage.
    
    Stores embeddings in FAISS index and metadata in separate JSON file.
    """
    
    def __init__(
        self,
        embeddings_provider: EmbeddingsProvider,
        index_path: Optional[Path] = None,
    ):
        """
        Initialize FAISS index manager.
        
        Args:
            embeddings_provider: Provider for generating embeddings
            index_path: Path to save/load index (without extension)
        """
        try:
            import faiss
        except ImportError:
            raise ImportError(
                "faiss-cpu is required for FAISSIndexManager. "
                "Install it with: pip install faiss-cpu"
            )
        
        self.faiss = faiss
        self.embeddings_provider = embeddings_provider
        self.index_path = index_path
        self.dimension = embeddings_provider.get_dimension()
        
        # Initialize empty index
        self.index = None
        self.metadata: List[Dict[str, Any]] = []
        self._create_index()
        
        logger.info(f"FAISS index manager initialized with dimension {self.dimension}")
    
    def _create_index(self):
        """Create a new FAISS index."""
        # Use L2 distance (Euclidean) for similarity
        self.index = self.faiss.IndexFlatL2(self.dimension)
        logger.debug("Created new FAISS index")
    
    def add_chunks(self, chunks: List[TextChunk]) -> None:
        """
        Add text chunks to the index.
        
        Args:
            chunks: List of TextChunk objects to add
        """
        if not chunks:
            logger.warning("No chunks provided to add")
            return
        
        logger.info(f"Adding {len(chunks)} chunks to index")
        
        # Extract text from chunks
        texts = [chunk.text for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.embeddings_provider.embed_batch(texts)
        
        # Add to FAISS index
        self.index.add(embeddings.astype(np.float32))
        
        # Store metadata
        for chunk in chunks:
            self.metadata.append(chunk.to_dict())
        
        logger.info(f"Successfully added {len(chunks)} chunks. Total: {self.index.ntotal}")
    
    def search(
        self,
        query: str,
        k: int = 10,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search for similar chunks.
        
        Args:
            query: Query text
            k: Number of results to return
            
        Returns:
            List of tuples containing (metadata, distance)
        """
        if self.index.ntotal == 0:
            logger.warning("Index is empty, no results to return")
            return []
        
        logger.debug(f"Searching for: {query[:50]}...")
        
        # Generate query embedding
        query_embedding = self.embeddings_provider.embed_text(query)
        query_embedding = query_embedding.reshape(1, -1).astype(np.float32)
        
        # Search in FAISS
        k = min(k, self.index.ntotal)  # Ensure k doesn't exceed total vectors
        distances, indices = self.index.search(query_embedding, k)
        
        # Collect results with metadata
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.metadata):
                results.append((self.metadata[idx], float(dist)))
        
        logger.debug(f"Found {len(results)} results")
        return results
    
    def save(self, path: Optional[Path] = None) -> None:
        """
        Save index and metadata to disk.
        
        Args:
            path: Path to save to (without extension). Uses self.index_path if None.
        """
        save_path = path or self.index_path
        if save_path is None:
            raise ValueError("No path specified for saving index")
        
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        index_file = str(save_path.with_suffix(".faiss"))
        self.faiss.write_index(self.index, index_file)
        logger.info(f"Saved FAISS index to {index_file}")
        
        # Save metadata
        metadata_file = str(save_path.with_suffix(".meta.json"))
        with open(metadata_file, "w") as f:
            json.dump(self.metadata, f, indent=2)
        logger.info(f"Saved metadata to {metadata_file}")
    
    def load(self, path: Optional[Path] = None) -> None:
        """
        Load index and metadata from disk.
        
        Args:
            path: Path to load from (without extension). Uses self.index_path if None.
        """
        load_path = path or self.index_path
        if load_path is None:
            raise ValueError("No path specified for loading index")
        
        load_path = Path(load_path)
        
        # Load FAISS index
        index_file = str(load_path.with_suffix(".faiss"))
        if not Path(index_file).exists():
            raise FileNotFoundError(f"Index file not found: {index_file}")
        
        self.index = self.faiss.read_index(index_file)
        logger.info(f"Loaded FAISS index from {index_file} ({self.index.ntotal} vectors)")
        
        # Load metadata
        metadata_file = str(load_path.with_suffix(".meta.json"))
        if not Path(metadata_file).exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_file}")
        
        with open(metadata_file, "r") as f:
            self.metadata = json.load(f)
        logger.info(f"Loaded metadata from {metadata_file} ({len(self.metadata)} entries)")
        
        # Verify consistency
        if self.index.ntotal != len(self.metadata):
            logger.warning(
                f"Mismatch: index has {self.index.ntotal} vectors "
                f"but metadata has {len(self.metadata)} entries"
            )
    
    def update(self, chunks: List[TextChunk]) -> None:
        """
        Update index with new chunks (adds to existing index).
        
        Args:
            chunks: List of TextChunk objects to add
        """
        logger.info(f"Updating index with {len(chunks)} new chunks")
        self.add_chunks(chunks)
    
    def rebuild(self, chunks: List[TextChunk]) -> None:
        """
        Rebuild index from scratch with new chunks.
        
        Args:
            chunks: List of TextChunk objects
        """
        logger.info(f"Rebuilding index with {len(chunks)} chunks")
        self._create_index()
        self.metadata = []
        self.add_chunks(chunks)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the index.
        
        Returns:
            Dictionary with index statistics
        """
        return {
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "metadata_count": len(self.metadata),
        }
