"""LLM service for generating answers using OpenAI."""
import os
from typing import List, Dict, Any
from openai import OpenAI


class LLMService:
    """Service for generating answers using LLM."""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """Initialize LLM service.
        
        Args:
            model: OpenAI model to use
        """
        self.model = model
    
    def generate_answer(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]]
    ) -> str:
        """Generate an answer to a question based on context chunks.
        
        Args:
            question: User's question
            context_chunks: Relevant document chunks with metadata
            
        Returns:
            Generated answer
        """
        # Build context from chunks
        context = "\n\n".join([
            f"[Source: {chunk['metadata']['title']}]\n{chunk['text']}"
            for chunk in context_chunks
        ])
        
        # Create prompt
        prompt = f"""You are a helpful research assistant. Answer the user's question based on the provided context from research documents.

Context from documents:
{context}

Question: {question}

Instructions:
- Provide a clear, accurate answer based on the context
- If the context doesn't contain enough information, say so
- Cite which documents you're referencing when possible
- Be concise but thorough

Answer:"""
        
        # Prefer OpenAI if API key is available; otherwise fall back to extractive answer
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful research assistant that answers questions based on provided document context."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                return response.choices[0].message.content
            except Exception:
                # Fall through to extractive answer
                pass
        # Fallback: return a concise extractive response from provided context
        try:
            if not context_chunks:
                return "I couldn't find relevant information in the uploaded documents to answer your question."
            # Assemble top chunks into a simple answer
            joined = "\n\n".join(chunk["text"] for chunk in context_chunks[:3])
            return f"Based on the provided documents, here are relevant excerpts:\n\n{joined}"
        except Exception as e:
            raise Exception(f"Error generating answer (fallback): {str(e)}")

