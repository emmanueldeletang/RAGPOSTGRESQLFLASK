from openai import OpenAI
from config import Config
import numpy as np

class EmbeddingService:
    """Service for generating embeddings using OpenAI"""
    
    def __init__(self):
        self.config = Config()
        self.client = OpenAI(api_key=self.config.OPENAI_API_KEY)
        self.model = self.config.EMBEDDING_MODEL
    
    def get_embedding(self, text: str):
        """
        Generate embedding for a text
        
        Args:
            text: The text to embed
            
        Returns:
            List of floats representing the embedding
        """
        if not text or not text.strip():
            return None
        
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.model
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise
    
    def get_embeddings_batch(self, texts: list):
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings
        """
        if not texts:
            return []
        
        try:
            # Filter out empty texts
            valid_texts = [t for t in texts if t and t.strip()]
            if not valid_texts:
                return []
            
            response = self.client.embeddings.create(
                input=valid_texts,
                model=self.model
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            raise
