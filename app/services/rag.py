import google.generativeai as genai
from typing import List
from sqlalchemy.orm import Session
from app.models.models import Chunk
from app.core.config import settings

class RAGService:
    def __init__(self, db: Session):
        self.db = db
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            # Using 2.5-flash as it is the newest and likely has better availability
            self.model = genai.GenerativeModel('models/gemini-2.5-flash')
        else:
            self.model = None

    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding using Gemini"""
        if not self.model:
            return [0.1] * 768 # Mock
            
        result = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_document",
            title="Embedding of text"
        )
        return result['embedding']

    async def search(self, agent_id: str, query: str, limit: int = 5) -> List[Chunk]:
        """
        Semantic search. 
        For MVP without vector DB, we'll still do a basic DB fetch 
        but in a real app we'd use the embedding to query PGVector.
        """
        # In a real implementation:
        # query_embedding = await self.get_embedding(query)
        # return db.query(Chunk).order_by(Chunk.embedding.cosine_distance(query_embedding)).limit(limit)
        
        chunks = self.db.query(Chunk)\
            .filter(Chunk.agent_id == agent_id)\
            .limit(limit)\
            .all()
        return chunks

    async def generate_answer(self, query: str, context: List[Chunk]) -> str:
        """Generate answer using Gemini with retry"""
        if not context:
            return "I don't have enough information to answer that."
            
        context_str = "\n\n".join([f"Source ({c.page_url}): {c.content}" for c in context])
        
        prompt = f"""You are a helpful AI assistant for a business. 
Answer the user's question based on the following context. 
If the user greets you (e.g., 'hi', 'hello'), respond politely.
For specific questions, if the answer is not in the context, say you don't know.

Context:
{context_str}

User Question: {query}
"""
        
        if self.model:
            import asyncio
            from google.api_core.exceptions import ResourceExhausted
            
            retries = 3
            for i in range(retries):
                try:
                    response = self.model.generate_content(prompt)
                    print(f"\n[DEBUG] Gemini Response: {response.text}\n")
                    return response.text
                except ResourceExhausted:
                    if i == retries - 1:
                        return "I'm currently overloaded with requests. Please try again in a moment."
                    await asyncio.sleep(2 * (i + 1)) # Exponential backoff
            return "Error generating response."
        else:
            return f"[MOCK GEMINI] Based on context: {context_str[:100]}..."

    async def generate_answer_stream(self, query: str, context: List[Chunk]):
        """Generate answer using Gemini with streaming"""
        if not context:
            yield "I don't have enough information to answer that."
            return

        context_str = "\n\n".join([f"Source ({c.page_url}): {c.content}" for c in context])
        
        prompt = f"""You are a knowledgeable and helpful employee of the company. 
Answer the user's question naturally and professionally, as if you are speaking directly to a customer.
Do NOT mention "context", "provided text", or "documents". Use the information provided below as if it is your own knowledge.

If the user greets you (e.g., 'hi', 'hello'), respond politely and professionally.
If the answer is not in the information below, politely say you don't have that information right now.

Information:
{context_str}

User Question: {query}
"""
        
        if self.model:
            try:
                response = self.model.generate_content(prompt, stream=True)
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
            except Exception as e:
                print(f"Streaming error: {e}")
                yield "Error generating response."
        else:
            yield f"[MOCK GEMINI] Based on context: {context_str[:100]}..."
