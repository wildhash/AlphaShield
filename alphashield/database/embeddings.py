"""Voyage AI embeddings for semantic context sharing between agents."""
import os
from typing import List, Optional
import voyageai


class EmbeddingsClient:
    """Voyage AI client for generating embeddings."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Voyage AI client.
        
        Args:
            api_key: Voyage API key. If None, reads from env.
        """
        self.api_key = api_key or os.getenv('VOYAGE_API_KEY')
        if not self.api_key:
            raise ValueError("Voyage API key not provided")
        
        self.client = voyageai.Client(api_key=self.api_key)
        
    def embed_text(self, text: str, model: str = "voyage-2") -> List[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Text to embed
            model: Voyage model to use
            
        Returns:
            Embedding vector as list of floats.
        """
        result = self.client.embed([text], model=model)
        return result.embeddings[0]
    
    def embed_batch(self, texts: List[str], model: str = "voyage-2") -> List[List[float]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            model: Voyage model to use
            
        Returns:
            List of embedding vectors.
        """
        result = self.client.embed(texts, model=model)
        return result.embeddings
    
    def cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score between -1 and 1.
        """
        import numpy as np
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
