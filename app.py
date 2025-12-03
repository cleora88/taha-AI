from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime

# Import services (we'll create these next)
from services.pdf_processor import extract_text_from_pdf, chunk_text
from services.embedding_service import create_embeddings
from services.vector_db import VectorDB
from services.llm_service import LLMService

load_dotenv()

app = FastAPI(title="Research Assistant API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
vector_db = VectorDB()
llm_service = LLMService()

# In-memory storage for document metadata (use MongoDB/PostgreSQL in production)
documents_db = {}
chat_history_db = {}

# Models
class ChatRequest(BaseModel):
    question: str
    user_id: str = "default_user"

class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]
    chat_id: str

class DocumentInfo(BaseModel):
    document_id: str
    title: str
    upload_date: str
    total_chunks: int

@app.get("/")
def root():
    return {"message": "Research Assistant API is running"}

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a PDF document"""
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Generate unique document ID
        doc_id = str(uuid.uuid4())
        
        # Read file content
        content = await file.read()
        
        # Save file temporarily (use OS temp directory)
        import tempfile
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"{doc_id}.pdf")
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # Extract text from PDF
        text = extract_text_from_pdf(temp_path)
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        
        # Split text into chunks
        chunks = chunk_text(text)
        
        # Create embeddings
        embeddings = create_embeddings(chunks)
        
        # Store in vector database
        vector_db.store_document(
            document_id=doc_id,
            chunks=chunks,
            embeddings=embeddings,
            metadata={
                "title": file.filename,
                "upload_date": datetime.now().isoformat()
            }
        )
        
        # Store document metadata
        documents_db[doc_id] = {
            "document_id": doc_id,
            "title": file.filename,
            "upload_date": datetime.now().isoformat(),
            "total_chunks": len(chunks)
        }
        
        # Clean up temporary file
        os.remove(temp_path)
        
        return {
            "document_id": doc_id,
            "title": file.filename,
            "chunks_processed": len(chunks),
            "message": "Document uploaded and processed successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.get("/api/documents/")
def list_documents():
    """List all uploaded documents"""
    return {"documents": list(documents_db.values())}

@app.delete("/api/documents/{document_id}")
def delete_document(document_id: str):
    """Delete a document and its embeddings"""
    try:
        if document_id not in documents_db:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete from vector database
        vector_db.delete_document(document_id)
        
        # Delete from metadata storage
        del documents_db[document_id]
        
        return {"message": "Document deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@app.post("/api/chat/ask", response_model=ChatResponse)
async def ask_question(request: ChatRequest):
    """Ask a question about uploaded documents"""
    try:
        if not documents_db:
            raise HTTPException(status_code=400, detail="No documents uploaded yet")
        
        # Create embedding for the question
        question_embedding = create_embeddings([request.question])[0]
        
        # Search vector database for relevant chunks
        relevant_chunks = vector_db.search(
            query_embedding=question_embedding,
            top_k=5
        )
        
        if not relevant_chunks:
            return ChatResponse(
                answer="I couldn't find relevant information in the uploaded documents to answer your question.",
                sources=[],
                chat_id=str(uuid.uuid4())
            )
        
        # Generate answer using LLM
        answer = llm_service.generate_answer(
            question=request.question,
            context_chunks=relevant_chunks
        )
        
        # Format sources
        sources = [
            {
                "document_id": chunk["metadata"]["document_id"],
                "document_title": chunk["metadata"]["title"],
                "chunk_text": chunk["text"][:200] + "...",
                "score": chunk["score"]
            }
            for chunk in relevant_chunks
        ]
        
        # Store in chat history
        chat_id = str(uuid.uuid4())
        chat_history_db[chat_id] = {
            "chat_id": chat_id,
            "user_id": request.user_id,
            "question": request.question,
            "answer": answer,
            "sources": sources,
            "timestamp": datetime.now().isoformat()
        }
        
        return ChatResponse(
            answer=answer,
            sources=sources,
            chat_id=chat_id
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.get("/api/chat/history")
def get_chat_history(user_id: str = "default_user"):
    """Get chat history for a user"""
    user_chats = [
        chat for chat in chat_history_db.values()
        if chat["user_id"] == user_id
    ]
    return {"history": sorted(user_chats, key=lambda x: x["timestamp"], reverse=True)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)