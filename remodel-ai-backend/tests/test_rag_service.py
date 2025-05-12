import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
sys.path.append('..')  # Add parent directory to path
@patch('services.rag_service.PineconeClient')
@patch('services.rag_service.OpenAIEmbeddings')
@patch('services.rag_service.ChatOpenAI')
@patch('services.rag_service.Pinecone')
def test_rag_service_init(mock_pinecone_store, mock_chat, mock_embeddings, mock_pinecone):
    """Test RAG service initialization"""
    # Mock the Pinecone client
    mock_pc_instance = MagicMock()
    mock_pinecone.return_value = mock_pc_instance
    # Mock the index
    mock_index = MagicMock()
    mock_pc_instance.Index.return_value = mock_index
    # Import here to avoid issues with patching
    from services.rag_service import RAGService
    # Create service
    service = RAGService()
    assert service is not None
    mock_embeddings.assert_called_once()
    mock_pinecone.assert_called_once()