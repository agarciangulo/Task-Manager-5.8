from src.core.embedding_manager import EmbeddingManager
from src.core.exceptions import handle_agent_errors, EmbeddingAgentError

class EmbeddingAgent:
    """Agent for embedding generation and management."""
    def __init__(self):
        self.manager = EmbeddingManager()

    @handle_agent_errors("EmbeddingAgent")
    def get_embedding(self, text):
        try:
            return self.manager.get_embedding(text)
        except Exception as e:
            raise EmbeddingAgentError(f"Failed to get embedding: {e}")

    @handle_agent_errors("EmbeddingAgent")
    def get_batch_embeddings(self, texts, force_refresh=False):
        try:
            return self.manager.get_batch_embeddings(texts, force_refresh=force_refresh)
        except Exception as e:
            raise EmbeddingAgentError(f"Failed to get batch embeddings: {e}") 