"""Vector database service using FAISS."""
import faiss
import numpy as np
from typing import List, Dict, Any
import pickle
import os


class VectorDB:
    """Vector database wrapper using FAISS with dynamic dimensions."""
    
    def __init__(self):
        """Initialize FAISS index lazily based on first embeddings added."""
        self.dimension = None
        self.index = None
        self.documents = []
        self.metadatas = []
        self.storage_path = os.path.join(os.getcwd(), "faiss_storage.pkl")
    
    def store_document(
        self,
        document_id: str,
        chunks: List[str],
        embeddings: List[List[float]],
        metadata: Dict[str, Any]
    ):
        """Store document chunks and embeddings in the vector database.
        
        Args:
            document_id: Unique identifier for the document
            chunks: List of text chunks
            embeddings: List of embedding vectors
            metadata: Document metadata (title, upload_date, etc.)
        """
        # Convert embeddings to numpy array and normalize for cosine similarity
        embeddings_array = np.array(embeddings, dtype=np.float32)
        # Initialize index on first use
        if self.index is None:
            self.dimension = embeddings_array.shape[1]
            self.index = faiss.IndexFlatIP(self.dimension)
        # Normalize to use cosine similarity via inner product
        faiss.normalize_L2(embeddings_array)
        self.index.add(embeddings_array)
        
        # Store documents and metadata
        for i, chunk in enumerate(chunks):
            self.documents.append(chunk)
            self.metadatas.append({
                "document_id": document_id,
                "title": metadata.get("title", ""),
                "upload_date": metadata.get("upload_date", ""),
                "chunk_index": i
            })
        
        # Save to disk
        self._save_to_disk()
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks using a query embedding.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of top results to return
            
        Returns:
            List of matching chunks with metadata and scores
        """
        if self.index is None or self.index.ntotal == 0:
            return []
        
        # Convert query to numpy array and normalize
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        top_k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_array, top_k)
        
        # Format results
        formatted_results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.documents):
                formatted_results.append({
                    "text": self.documents[idx],
                    "metadata": self.metadatas[idx],
                    "score": float(score)
                })
        
        return formatted_results
    
    def delete_document(self, document_id: str):
        """Delete all chunks associated with a document.
        
        Args:
            document_id: Document identifier
        """
        # Find indices to remove
        indices_to_keep = []
        docs_to_keep = []
        metas_to_keep = []
        
        for i, meta in enumerate(self.metadatas):
            if meta["document_id"] != document_id:
                indices_to_keep.append(i)
                docs_to_keep.append(self.documents[i])
                metas_to_keep.append(meta)
        
        # Rebuild index if we removed any documents
        if len(indices_to_keep) < len(self.documents):
            self.documents = docs_to_keep
            self.metadatas = metas_to_keep
            
            # Rebuild FAISS index
            if self.dimension:
                self.index = faiss.IndexFlatIP(self.dimension)
            
            self._save_to_disk()
    
    def _save_to_disk(self):
        """Save index and data to disk."""
        try:
            with open(self.storage_path, 'wb') as f:
                pickle.dump({
                    'documents': self.documents,
                    'metadatas': self.metadatas
                }, f)
            faiss.write_index(self.index, self.storage_path.replace('.pkl', '.index'))
        except Exception as e:
            print(f"Warning: Could not save to disk: {e}")
    
    def _load_from_disk(self):
        """Load index and data from disk."""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'rb') as f:
                    data = pickle.load(f)
                    self.documents = data['documents']
                    self.metadatas = data['metadatas']
            
            index_path = self.storage_path.replace('.pkl', '.index')
            if os.path.exists(index_path):
                self.index = faiss.read_index(index_path)
        except Exception as e:
            print(f"Warning: Could not load from disk: {e}")

        results = self.collection.get(
            where={"document_id": document_id}
        )
        
        if results['ids']:
            self.collection.delete(ids=results['ids'])
