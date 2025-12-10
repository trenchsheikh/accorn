import uuid
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.core.database import get_db, engine, Base
from app.models.models import Agent, User, ScrapeJob
from app.schemas.schemas import AgentCreate, AgentResponse, QueryRequest, QueryResponse, ScrapeStatus
from app.worker.scraper import ScraperWorker

# Create tables (for MVP simplicity, use Alembic in prod)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Acorn API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def run_scraper_task(job_id: str):
    worker = ScraperWorker(job_id)
    await worker.run()

@app.post("/v1/onboard", response_model=AgentResponse)
def onboard(agent_in: AgentCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # 1. Create or get user
    user = db.query(User).filter(User.email == agent_in.email).first()
    if not user:
        user = User(email=agent_in.email, name=agent_in.name)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # 2. Create Agent
    agent = Agent(
        owner_id=user.id,
        root_url=str(agent_in.root_url),
        domain=str(agent_in.root_url), # Simplified
        status="pending",
        public_key=str(uuid.uuid4())
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    
    # 3. Create Scrape Job
    job = ScrapeJob(
        agent_id=agent.id,
        root_url=str(agent_in.root_url),
        status="queued"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # 4. Trigger Worker
    background_tasks.add_task(run_scraper_task, str(job.id))
    
    return agent

@app.get("/v1/agents/{agent_id}/status", response_model=ScrapeStatus)
def get_status(agent_id: str, db: Session = Depends(get_db)):
    try:
        real_id = uuid.UUID(agent_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    agent = db.query(Agent).filter(Agent.id == real_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Get latest job
    job = db.query(ScrapeJob).filter(ScrapeJob.agent_id == agent_id).order_by(ScrapeJob.created_at.desc()).first()
    
    return ScrapeStatus(
        status=agent.status if not job else job.status,
        pages_scraped=0 if not job else job.pages_scraped,
        total_pages=0 if not job else job.total_pages
    )

from app.services.rag import RAGService
from app.services.voice import VoiceService

from fastapi.responses import FileResponse, StreamingResponse
import json

@app.post("/v1/agents/{agent_id}/query")
async def query_agent(agent_id: str, query_in: QueryRequest, db: Session = Depends(get_db)):
    if agent_id == "demo-agent-id":
        # Mock stream for demo
        async def demo_stream():
            msg = "I am a demo agent. To get real responses based on a website, please onboard a new agent using the /onboard endpoint."
            for word in msg.split():
                yield json.dumps({"type": "text", "content": word + " "}) + "\n"
                import asyncio
                await asyncio.sleep(0.05)
            yield json.dumps({"type": "done"}) + "\n"
        return StreamingResponse(demo_stream(), media_type="application/x-ndjson")
        
    try:
        real_id = uuid.UUID(agent_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid Agent ID format")
        
    rag = RAGService(db)
    voice = VoiceService()
    
    # 1. Search
    chunks = await rag.search(real_id, query_in.query)
    
    async def response_generator():
        import re
        sentence_buffer = ""
        
        # 2. Generate Stream
        async for text_chunk in rag.generate_answer_stream(query_in.query, chunks):
            # Yield text event for UI immediately
            yield json.dumps({"type": "text", "content": text_chunk}) + "\n"
            
            sentence_buffer += text_chunk
            
            # Check for sentence delimiters (., !, ?) followed by space or end of string
            # This is a simple heuristic to send audio in chunks for lower latency
            if re.search(r'[.!?](\s+|$)', sentence_buffer):
                audio_base64 = voice.generate_audio(sentence_buffer)
                if audio_base64:
                    yield json.dumps({"type": "audio_chunk", "content": audio_base64}) + "\n"
                sentence_buffer = ""
            
        # Process any remaining text in buffer
        if sentence_buffer.strip():
            audio_base64 = voice.generate_audio(sentence_buffer)
            if audio_base64:
                yield json.dumps({"type": "audio_chunk", "content": audio_base64}) + "\n"
        
        # 4. Sources
        sources = [{"url": c.page_url, "content": c.content[:100]} for c in chunks]
        yield json.dumps({"type": "sources", "content": sources}) + "\n"
        yield json.dumps({"type": "done"}) + "\n"

    return StreamingResponse(response_generator(), media_type="application/x-ndjson")

@app.get("/widget.js")
def get_widget():
    return FileResponse("widget/widget.js", media_type="application/javascript")

@app.get("/demo")
def get_demo():
    return FileResponse("demo/index.html")
