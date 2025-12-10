Full detailed plan — RAG-Optimised Deep Scraper + Voice Receptionist (Python-first, production-ready)

Nice — below is a comprehensive, actionable plan you can hand to an engineer or use yourself. I pick Python (best for scraping + pipelines) but include notes where Node.js alternatives fit. The plan covers architecture, data schema, scraping, chunking, embedding, indexing, RAG pipeline, voice stack, embeddable widget, deployment, testing, monitoring, and an incremental roadmap (MVP → full product). Each section contains exact libraries, endpoints, file layout, example payloads, and acceptance criteria.

⸻

1 — High-level architecture (components)
	1.	Onboarding Service (Web UI)
	•	Paste URL → starts a scrape job → shows progress → returns AGENT_ID + embed snippet.
	2.	Scraper Worker
	•	Deep crawl (Playwright) + extraction + cleaning + structured extraction + chunking + summarisation.
	3.	Indexer Service
	•	Create embeddings → push to Vector DB (Pinecone or Qdrant) + store metadata in Postgres.
	4.	RAG API (Query Service)
	•	Receives user query/audio → transcribe → vector search → LLM call → synthesize TTS → stream response.
	5.	Widget Static JS
	•	Embeddable <script> that opens UI, records audio, streams via WebSocket to RAG API, renders text + plays TTS.
	6.	Admin Dashboard
	•	Agents list, scrape logs, freshness, analytics, missed questions editor.
	7.	Integrations
	•	Webhooks (CRM), Email, Zapier, WhatsApp handoff.

⸻

2 — Tech stack (recommended)
	•	Language: Python 3.11
	•	Scraping / Rendering: Playwright (sync or async)
	•	Parsing: BeautifulSoup4, readability-lxml
	•	NLP & LLM: OpenAI (GPT-5.1 / text-embedding-3-large) or local LLM option (LlamaX)
	•	Embedding Vector DB: Pinecone or Qdrant (Pinecone recommended for hosted ease)
	•	DB: PostgreSQL (Supabase optional)
	•	Backend framework: FastAPI (async)
	•	Realtime: WebSockets (FastAPI / Uvicorn)
	•	TTS / STT: Whisper API / OpenAI for STT; ElevenLabs or PlayHT for TTS (or cloud TTS)
	•	Frontend (widget + admin): Vanilla JS for the widget ( ~10kb), React for admin.
	•	Hosting: Railway / Render / Fly.io for MVP, AWS (ECS/Fargate) for scale
	•	CI/CD: GitHub Actions
	•	Monitoring: Sentry + Prometheus/Grafana (optional)
	•	Container: Docker

Node.js alternative: Playwright, Puppeteer, TypeScript backend (Nest/Express), same vector DB.

⸻

3 — Data & JSON schemas

3.1 — Complete PostgreSQL Database Schema

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users/Owners table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agents table
CREATE TABLE agents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
  domain TEXT NOT NULL,
  root_url TEXT NOT NULL,
  name VARCHAR(255),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  last_scraped TIMESTAMPTZ,
  status VARCHAR(50) DEFAULT 'pending', -- pending / scraping / ready / failed
  config JSONB DEFAULT '{}',
  public_key VARCHAR(255) UNIQUE, -- For widget authentication
  created_by UUID REFERENCES users(id),
  CONSTRAINT status_check CHECK (status IN ('pending', 'scraping', 'ready', 'failed'))
);

-- Scrape jobs table
CREATE TABLE scrape_jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
  root_url TEXT NOT NULL,
  status VARCHAR(50) DEFAULT 'queued', -- queued / running / completed / failed
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  pages_scraped INTEGER DEFAULT 0,
  total_pages INTEGER,
  error_message TEXT,
  config JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Chunks metadata table (mirror of vector DB for lineage)
CREATE TABLE chunks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
  chunk_id VARCHAR(255) UNIQUE NOT NULL, -- Vector DB ID
  page_url TEXT NOT NULL,
  content TEXT,
  token_count INTEGER,
  metadata JSONB DEFAULT '{}',
  importance_score FLOAT DEFAULT 0.0,
  category VARCHAR(100),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Conversations table (for analytics)
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
  session_id VARCHAR(255),
  query_text TEXT,
  query_audio_url TEXT,
  response_text TEXT,
  response_audio_url TEXT,
  sources JSONB, -- Array of chunk IDs and URLs
  latency_ms INTEGER,
  satisfaction_score INTEGER, -- 1-5 rating
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- FAQs table (auto-generated + manual)
CREATE TABLE faqs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  source_chunk_ids TEXT[],
  is_auto_generated BOOLEAN DEFAULT TRUE,
  is_approved BOOLEAN DEFAULT FALSE,
  usage_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Analytics table
CREATE TABLE analytics (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
  metric_type VARCHAR(100), -- 'query', 'missed_question', 'error'
  metric_value JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_agents_owner_id ON agents(owner_id);
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_public_key ON agents(public_key);
CREATE INDEX idx_chunks_agent_id ON chunks(agent_id);
CREATE INDEX idx_chunks_category ON chunks(category);
CREATE INDEX idx_conversations_agent_id ON conversations(agent_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);
CREATE INDEX idx_faqs_agent_id ON faqs(agent_id);
CREATE INDEX idx_scrape_jobs_agent_id ON scrape_jobs(agent_id);
CREATE INDEX idx_scrape_jobs_status ON scrape_jobs(status);
```

3.2 — Agent Configuration Schema (JSONB in agents.config)

```json
{
  "voice": {
    "provider": "elevenlabs", // or "openai", "playht"
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "stability": 0.5,
    "similarity_boost": 0.75
  },
  "personality": {
    "tone": "professional", // professional, friendly, casual
    "response_style": "concise", // concise, detailed, conversational
    "greeting": "Hello! How can I help you today?",
    "fallback_message": "I don't have that information. Would you like me to connect you with the team?"
  },
  "scraping": {
    "max_depth": 3,
    "max_pages": 50,
    "respect_robots_txt": true,
    "delay_seconds": 1.0
  },
  "rag": {
    "top_k": 8,
    "temperature": 0.1,
    "max_tokens": 500,
    "include_sources": true
  },
  "integrations": {
    "webhook_url": null,
    "crm_type": null, // "salesforce", "hubspot", etc.
    "capture_leads": false
  }
}
```

Output JSON for scraped data (file / API)

{
  "agent_id": "uuid",
  "root_url": "https://example.com",
  "summary": "Business one-liner...",
  "structured_data": {
    "address": "string",
    "phones": ["string"],
    "emails": ["string"],
    "opening_hours": {"monday":"9-5"},
    "services":[{"name":"Service","price":"£","path":"/service"}]
  },
  "pages": [
    {
      "url": "https://example.com/service",
      "title": "Service Page",
      "depth": 1,
      "type": "service_page",
      "word_count": 450,
      "clean_text": "cleaned text here",
      "chunks": [
        {
          "chunk_id": "uuid",
          "content": "chunked text ...",
          "tokens": 420,
          "metadata": {
            "section": "pricing",
            "category": "pricing",
            "importance": 0.92
          }
        }
      ]
    }
  ],
  "auto_faqs": [{"q":"...","a":"..."}]
}


⸻

4 — Scraper design (deep, production-ready)

Goals
	•	Crawl up to MAX_PAGES (configurable, e.g. 50).
	•	Only follow same-domain internal links, obey robots.txt for default.
	•	Render JS via Playwright (configurable: headless / timeout / networkidle).
	•	Extract structured data and page sections using DOM and heuristics.
	•	Normalize and dedupe text.
	•	Rate-limit & politeness.

Worker flow (pseudo)
	1.	Accept job with agent_id + root_url.
	2.	Fetch robots.txt → allowed paths.
	3.	Initialize queue [(root_url, depth=0)]. visited = set().
	4.	While queue and pages_scraped < MAX_PAGES:
	•	Pop URL, render page (Playwright) with wait_until='networkidle'.
	•	Extract HTML → read meta, schema.org JSON-LD, <h*>, <p>, <li>, tables.
	•	Clean text with readability + remove nav/footer via heuristics.
	•	Run structured extractors: phone, emails, opening hours (regex + dictionary), address (libpostal optional).
	•	Identify section blocks using header boundaries (H1/H2/H3 → grouping).
	•	For each block → create chunk(s) using SmartChunker (below).
	•	Store page + chunks in temp store (Redis or local disk) for batching.
	•	Discover internal links (<a href>) → enqueue depth+1 if same domain.
	5.	When job completes, call summariser + FAQ generator, then hand off to indexer.

Important heuristics
	•	If schema.org available (LD+JSON), parse contactPoint, openingHoursSpecification first.
	•	Use text density to ignore menus and navbars.
	•	Use CSS selectors for common patterns (e.g., .faq, #hours, .price) if present.

⸻

5 — Smart chunking algorithm (critical for RAG)

Principles
	•	Aim chunk size ~ 400–700 tokens (approx 300–550 words).
	•	Chunk by semantic sections (headers) not fixed tokens.
	•	Preserve context: include preceding header as metadata/context in chunk.
	•	Attach rich metadata to each chunk.

Implementation (python)
	1.	Tokenize page text by sentences (use nltk or spacy).
	2.	Group sentences into the current section (header until next header).
	3.	For each section:
	•	If length < min_tokens → append to previous chunk (if semantically similar).
	•	If length > max_tokens → split by paragraph or sentence boundary into multiple chunks.
	4.	For each chunk compute:
	•	chunk_embedding (via embedding model)
	•	importance_score (heuristic: presence of contact info, price, header level)
	•	category (faq/pricing/service/contact) using small classifier (keyword rules + LLM fallback).
	5.	Store chunk with metadata and source_doc pointer.

⸻

6 — Auto-summarize & FAQ generation
	•	Use LLM (system prompt tuned) to summarise:
	•	Business summary (1–2 lines)
	•	Service summaries (per service chunk)
	•	Pricing summary
	•	Generate canonical FAQs: feed page chunks + summary and ask model to produce 10–20 likely Q/A pairs. Store as faq chunks with importance=1.0.

Prompt examples and temperature: very low temperature (0–0.2) to reduce hallucination.

⸻

7 — Indexing pipeline
	1.	Batch chunk embeddings using text-embedding-3-large (or equivalent).
	2.	Upsert to Vector DB:
	•	id = chunk_id
	•	vector = embedding
	•	metadata = {agent_id, url, title, chunk_meta...}
	3.	Keep a Postgres mirror table for chunk metadata and lineage to allow updates and deletions.

Indexing considerations:
	•	Use namespaces per agent_id in Pinecone (or collection in Qdrant).
	•	Use hybrid metadata + vector filtering for faster, precise retrieval (e.g., category='contact').

⸻

8 — RAG Query pipeline (real-time)

Endpoints
	•	POST /v1/agents/{agent_id}/query — text query (sync)
	•	POST /v1/agents/{agent_id}/voice — multipart audio upload or WebSocket streaming
	•	WS /v1/realtime/{agent_id} — bi-directional streaming (audio in, TTS/audio chunks out)

Flow for a user text query
	1.	Validate agent_id & rate limits.
	2.	Query prefilter:
	•	If question matches FAQ intent → return canonical FAQ answer (fast path).
	3.	Vector search:
	•	Use top_k 8; filter by agent_id.
	•	Re-rank by importance_score + BM25 (optional).
	4.	Compose LLM prompt:
	•	System prompt sets persona and guardrails (use business_summary, agent_config).
	•	Include retrieved chunk contents (shortened) + direct structured fields (phone/hours) as facts.
	•	Instruction: answer only from provided sources; if insufficient, say “I don’t know — contact X”.
	5.	Call LLM (low temperature).
	6.	Return text and optionally call TTS to produce audio.

Flow for voice (streaming)
	•	Use WebSocket: audio chunks → server buffers (or uses real-time STT) → once utterance ended, run the same pipeline and stream back TTS audio (or do audio streaming from model if available).

Prompt engineering (must)
	•	Provide source citations: include [[source:chunk_id | url]] metadata appended to answer for traceability.
	•	Add hallucination guardrail: Answer only using the facts provided in the sources. If not present, reply: "I don't have that info. Would you like me to hand this to the business?"

⸻

9 — Widget design & embed

One-line embed (deliver to user)

<script src="https://assets.yourdomain.com/agent-widget.js" data-agent="AGENT_ID" async></script>

Core features (widget)
	•	Floating mic button, click to open popup
	•	Voice & text modes
	•	Show typing/voice waveform state
	•	Show transcript + “source” link for each answer
	•	Option: capture lead (name/email/phone) and send webhook

Communication
	•	Widget connects to WS /v1/realtime/{agent_id}?key=PUBLIC_KEY with ephemeral tokens (server-side generate short-lived JWT).

Security
	•	Widget must never hold long-term secrets; use ephemeral keys rotated via backend.

⸻

10 — Admin Dashboard (acceptance features)
	•	List agents, status, last scraped date
	•	View scrape job logs + raw scraped JSON
	•	“Regenerate embeddings” button
	•	“Edit/approve FAQ answer” UI to patch indexed chunk (manual corrections)
	•	Analytics: conversation count, top intents, missed Qs, satisfaction score

⸻

11 — Deployment & Infrastructure

11.1 — MVP Deployment (Railway/Render)

**Railway Setup:**
1. Create Railway account and new project
2. Add PostgreSQL service (managed)
3. Add Redis service (managed)
4. Deploy API service:
   ```bash
   railway init
   railway link
   railway up
   ```
5. Deploy Worker service (separate service)
6. Set environment variables in Railway dashboard
7. Configure custom domain

**Render Setup:**
1. Create Render account
2. Create PostgreSQL database
3. Create Redis instance
4. Deploy API as Web Service
5. Deploy Worker as Background Worker
6. Configure environment variables

**Environment Variables Setup:**
- Copy `.env.example` to production secrets
- Use service-provided secrets management
- Never commit secrets to git

11.2 — Production Deployment (AWS)

**Architecture:**
- **ECS/Fargate**: API and Worker services
- **RDS PostgreSQL**: Managed database
- **ElastiCache Redis**: Job queue
- **S3**: Static assets, audio files, logs
- **CloudFront**: CDN for widget and assets
- **ALB**: Load balancer with SSL termination
- **Route53**: DNS management

**Terraform Configuration:**
```hcl
# ECS Cluster
resource "aws_ecs_cluster" "acorn" {
  name = "acorn-cluster"
}

# API Service
resource "aws_ecs_service" "api" {
  name            = "acorn-api"
  cluster         = aws_ecs_cluster.acorn.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 2
  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }
}
```

**CI/CD Pipeline (GitHub Actions):**
```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build and push Docker image
        run: |
          docker build -t acorn-api:${{ github.sha }} .
          docker push acorn-api:${{ github.sha }}
      - name: Deploy to ECS
        run: |
          aws ecs update-service --cluster acorn --service api --force-new-deployment
```

11.3 — Database Migrations

**Using Alembic:**
```bash
# Initialize
alembic init migrations

# Create migration
alembic revision --autogenerate -m "Add agents table"

# Apply migration
alembic upgrade head
```

**Migration Script:**
```python
# migrations/versions/001_initial_schema.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table('agents',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        # ... other columns
    )

def downgrade():
    op.drop_table('agents')
```

11.4 — Backup & Disaster Recovery

**Database Backups:**
- Automated daily backups (RDS automated backups)
- Retention: 30 days
- Point-in-time recovery enabled

**Vector DB Backups:**
- Export chunk metadata from Postgres (source of truth)
- Re-index from Postgres if needed

**Disaster Recovery Plan:**
1. Database: Restore from latest backup
2. Application: Redeploy from git
3. Vector DB: Re-index from Postgres chunks
4. Estimated RTO: 2-4 hours

11.5 — Scaling Strategy

**Horizontal Scaling:**
- API: Auto-scale based on CPU/memory (2-10 instances)
- Workers: Scale based on queue depth (1-5 workers)
- Database: Read replicas for analytics queries

**Vertical Scaling:**
- Upgrade instance types if CPU-bound
- Increase database instance size for larger datasets

**Caching:**
- Redis cache for frequently accessed agent configs
- CDN caching for static widget assets

11.6 — Cost Optimization

**Estimated Monthly Costs (MVP - 100 agents, 10k queries/month):**
- **Pinecone**: $50-100 (small index)
- **OpenAI**: $200-500 (embeddings + LLM calls)
- **PostgreSQL**: $25-50 (managed, small instance)
- **Redis**: $15-30 (managed, small instance)
- **Hosting (Railway/Render)**: $50-100
- **TTS (ElevenLabs)**: $50-200 (depends on usage)
- **Total**: ~$400-1000/month

**Cost Reduction Tips:**
- Cache embeddings for unchanged content
- Use GPT-3.5-turbo for simple queries
- Batch embedding generation
- Compress audio files
- Use CDN for static assets

11.7 — Security Hardening

**Network Security:**
- VPC isolation (AWS)
- Security groups (restrictive ingress)
- WAF for API protection
- DDoS protection (Cloudflare)

**Application Security:**
- HTTPS only (TLS 1.2+)
- Rate limiting per IP/API key
- Input validation and sanitization
- SQL injection prevention (parameterized queries)
- XSS prevention (CSP headers)

**Secrets Management:**
- Use AWS Secrets Manager or HashiCorp Vault
- Rotate API keys quarterly
- Never log secrets
- Use IAM roles (AWS) instead of access keys where possible

⸻

12 — Comprehensive Testing Plan

12.1 — Unit Tests

**test_chunker.py**
```python
import pytest
from app.services.chunker import SmartChunker

def test_chunk_by_sections():
    chunker = SmartChunker(min_tokens=400, max_tokens=700)
    text = "Long text content here..."
    headers = [{"level": 1, "text": "Introduction", "position": 0}]
    chunks = chunker.chunk_by_sections(text, headers)
    assert len(chunks) > 0
    assert all(400 <= c.token_count <= 700 for c in chunks)

def test_importance_scoring():
    chunker = SmartChunker()
    chunk = "Contact us at phone: 555-1234 or email@example.com"
    metadata = {"header_level": 1}
    score = chunker.compute_importance(chunk, metadata)
    assert score > 0.5  # Should be high due to contact info + H1
```

**test_extractor.py**
```python
from app.services.extractor import StructuredExtractor

def test_phone_extraction():
    extractor = StructuredExtractor()
    text = "Call us at 555-1234 or (555) 123-4567"
    phones = extractor.extract_phones(text)
    assert len(phones) >= 2

def test_schema_org_extraction():
    extractor = StructuredExtractor()
    html = '<script type="application/ld+json">{"@type": "LocalBusiness"}</script>'
    data = extractor.extract_schema_org(html)
    assert data is not None
```

12.2 — Integration Tests

**test_scraper_integration.py**
```python
import pytest
from app.workers.scraper_worker import ScraperWorker

@pytest.mark.integration
def test_static_site_scraping():
    """Test scraping a static HTML site"""
    worker = ScraperWorker()
    result = worker.scrape("https://example.com", max_pages=5)
    assert result['status'] == 'completed'
    assert result['pages_scraped'] > 0

@pytest.mark.integration
def test_js_site_scraping():
    """Test scraping a JavaScript-rendered site"""
    worker = ScraperWorker(use_playwright=True)
    result = worker.scrape("https://spa-example.com", max_pages=5)
    assert result['status'] == 'completed'

@pytest.mark.integration
def test_ecommerce_scraping():
    """Test scraping an e-commerce site"""
    worker = ScraperWorker()
    result = worker.scrape("https://shop-example.com", max_pages=10)
    # Verify product/service extraction
    assert any('price' in str(chunk.metadata) for chunk in result['chunks'])
```

12.3 — API Integration Tests

**test_api.py**
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_onboard_endpoint():
    response = client.post("/v1/onboard", json={
        "root_url": "https://example.com",
        "name": "Test Business"
    })
    assert response.status_code == 200
    assert "agent_id" in response.json()
    assert "embed_code" in response.json()

def test_query_endpoint():
    # First create agent
    onboard_response = client.post("/v1/onboard", json={
        "root_url": "https://example.com"
    })
    agent_id = onboard_response.json()["agent_id"]
    
    # Wait for scraping to complete (or mock)
    # Then test query
    response = client.post(f"/v1/agents/{agent_id}/query", json={
        "query": "What are your services?"
    })
    assert response.status_code == 200
    assert "answer" in response.json()
```

12.4 — Load Testing

**load_test.py** (using Locust)
```python
from locust import HttpUser, task, between

class WidgetUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def query_agent(self):
        self.client.post(
            "/v1/agents/test-agent-id/query",
            json={"query": "Test question"},
            headers={"Authorization": "Bearer test-token"}
        )
    
    @task(3)
    def health_check(self):
        self.client.get("/healthz")
```

Run: `locust -f load_test.py --users 100 --spawn-rate 10`

12.5 — Security Testing

- **Widget Security**: Verify no API keys exposed in client-side code
- **Rate Limiting**: Test rate limit enforcement (100 req/min per IP)
- **SQL Injection**: Test all database queries with malicious inputs
- **XSS Prevention**: Test widget for XSS vulnerabilities
- **CORS**: Verify CORS headers are properly configured
- **Authentication**: Test JWT token validation and expiration

12.6 — Test Coverage Goals

- Unit tests: >80% coverage
- Integration tests: All critical paths
- E2E tests: Onboarding → Scraping → Query flow
- Performance tests: <600ms p95 latency for text queries

⸻

13 — Monitoring & Operations

13.1 — Health Check Endpoints

**GET /healthz**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "database": "healthy",
    "vector_db": "healthy",
    "redis": "healthy"
  }
}
```

**GET /healthz/ready** (Kubernetes readiness probe)
**GET /healthz/live** (Kubernetes liveness probe)

13.2 — Metrics Collection

**Key Metrics to Track:**

1. **Scraping Metrics**
   - `scrape_jobs_total` (counter)
   - `scrape_jobs_duration_seconds` (histogram)
   - `pages_scraped_total` (counter)
   - `scrape_errors_total` (counter by error type)

2. **RAG Metrics**
   - `rag_queries_total` (counter)
   - `rag_query_latency_ms` (histogram)
   - `vector_search_latency_ms` (histogram)
   - `llm_call_latency_ms` (histogram)
   - `rag_errors_total` (counter)

3. **Voice Metrics**
   - `stt_requests_total` (counter)
   - `stt_latency_ms` (histogram)
   - `tts_requests_total` (counter)
   - `tts_latency_ms` (histogram)

4. **Business Metrics**
   - `conversations_total` (counter)
   - `satisfaction_score` (histogram, 1-5)
   - `missed_questions_total` (counter)

**Prometheus Metrics Example:**
```python
from prometheus_client import Counter, Histogram, Gauge

scrape_jobs_total = Counter('scrape_jobs_total', 'Total scrape jobs')
rag_query_latency = Histogram('rag_query_latency_ms', 'RAG query latency in ms')
active_agents = Gauge('active_agents', 'Number of active agents')
```

13.3 — Logging Strategy

**Structured Logging (JSON)**
```python
import logging
import json

logger = logging.getLogger(__name__)

def log_scrape_job(agent_id: str, status: str, pages: int):
    logger.info(json.dumps({
        "event": "scrape_job_completed",
        "agent_id": agent_id,
        "status": status,
        "pages_scraped": pages,
        "timestamp": datetime.utcnow().isoformat()
    }))
```

**Log Levels:**
- ERROR: Failures, exceptions
- WARN: Rate limits, retries
- INFO: Job completion, important events
- DEBUG: Detailed debugging (disable in production)

13.4 — Alerting Rules

**Critical Alerts:**
- Error rate > 5% for 5 minutes
- P95 latency > 2 seconds for 10 minutes
- Database connection failures
- Vector DB unavailable
- Scrape job failure rate > 20%

**Warning Alerts:**
- High OpenAI API costs (threshold: $X/day)
- Low satisfaction scores (<3.0 average)
- High missed question rate (>10%)

**Alert Channels:**
- PagerDuty for critical alerts
- Slack for warnings
- Email for daily summaries

13.5 — Dashboards (Grafana)

**Dashboard Panels:**
1. System Health: Service status, uptime
2. Scraping: Jobs/min, success rate, avg duration
3. RAG Performance: Query latency, error rate, top queries
4. Voice: STT/TTS latency, audio quality metrics
5. Business: Conversations/day, satisfaction, top FAQs
6. Costs: OpenAI usage, infrastructure costs

13.6 — Operational Procedures

**Daily Checks:**
- Review error logs
- Check scrape job success rates
- Monitor API costs
- Review customer satisfaction scores

**Weekly Reviews:**
- Analyze missed questions
- Review and approve auto-generated FAQs
- Performance optimization opportunities
- Cost optimization review

**Incident Response:**
1. Identify issue (monitoring alert or user report)
2. Check health endpoints and logs
3. Isolate affected service
4. Apply fix or rollback
5. Post-mortem documentation

⸻

14 — Detailed Roadmap & Implementation Checklist

14.1 — MVP Phase (Week 1-2, 1 developer)

**Day 1-2: Project Setup**
- [ ] Initialize git repository
- [ ] Set up Python virtual environment
- [ ] Create project structure
- [ ] Set up PostgreSQL database (local)
- [ ] Create database schema (run migrations)
- [ ] Set up environment variables
- [ ] Create Docker Compose for local development
- [ ] Set up basic FastAPI app with health endpoint

**Day 3-4: Scraper Implementation**
- [ ] Install and configure Playwright
- [ ] Implement basic page scraper (single page)
- [ ] Add robots.txt parsing
- [ ] Implement link discovery (same-domain only)
- [ ] Add text extraction and cleaning
- [ ] Implement structured data extraction (phones, emails, addresses)
- [ ] Add schema.org JSON-LD parsing
- [ ] Test on 3 different site types

**Day 5-6: Chunking & Embedding**
- [ ] Implement SmartChunker class
- [ ] Add section-based chunking (header-aware)
- [ ] Implement importance scoring
- [ ] Set up OpenAI embeddings client
- [ ] Generate embeddings for chunks
- [ ] Test chunk quality and token counts

**Day 7-8: Vector DB & Indexing**
- [ ] Set up Pinecone account and index
- [ ] Implement VectorIndexer service
- [ ] Create chunk upsert logic
- [ ] Set up Postgres chunks table (metadata mirror)
- [ ] Implement batch indexing
- [ ] Test retrieval with sample queries

**Day 9-10: RAG Pipeline**
- [ ] Implement RAGService class
- [ ] Add vector search with filtering
- [ ] Create LLM prompt templates
- [ ] Implement query endpoint (POST /v1/agents/{id}/query)
- [ ] Add source citation in responses
- [ ] Test accuracy on sample questions

**Day 11-12: Onboarding & Basic UI**
- [ ] Implement onboarding endpoint (POST /v1/onboard)
- [ ] Create job queue system (Redis + RQ)
- [ ] Build simple onboarding HTML page
- [ ] Add job status endpoint
- [ ] Generate embed code with agent ID
- [ ] Test full flow: onboard → scrape → query

**Day 13-14: Voice Integration (Basic)**
- [ ] Set up ElevenLabs TTS account
- [ ] Implement TTS service
- [ ] Add voice endpoint (POST /v1/agents/{id}/voice)
- [ ] Implement audio file upload (multipart)
- [ ] Add Whisper STT integration
- [ ] Create simple widget (record → upload → play)
- [ ] Test voice query flow

**MVP Acceptance Criteria:**
- [x] Can create agent from any website URL
- [x] Scraper successfully crawls 5-10 pages
- [x] Chunks are properly indexed in Pinecone
- [x] Text queries return accurate answers with sources
- [x] Voice queries work (upload → transcribe → answer → TTS)
- [x] Widget can be embedded and used on test site

14.2 — v1 Production Phase (Week 3-6, 1-2 developers)

**Week 3: Deep Crawling & Robustness**
- [ ] Increase max pages to 50, depth to 3
- [ ] Implement deduplication logic
- [ ] Add retry mechanism for failed pages
- [ ] Implement rate limiting per domain
- [ ] Add better error handling and logging
- [ ] Create scrape job status tracking
- [ ] Add job cancellation capability

**Week 4: Real-time Voice**
- [ ] Implement WebSocket endpoint (/v1/realtime/{agent_id})
- [ ] Add streaming STT (real-time transcription)
- [ ] Implement streaming TTS response
- [ ] Update widget for WebSocket connection
- [ ] Add audio chunk buffering
- [ ] Implement connection management
- [ ] Add reconnection logic

**Week 5: Admin Dashboard**
- [ ] Create React admin dashboard
- [ ] Implement agent list view
- [ ] Add scrape job logs viewer
- [ ] Create FAQ editor (edit/approve answers)
- [ ] Add analytics dashboard (conversations, top queries)
- [ ] Implement "Regenerate embeddings" feature
- [ ] Add user authentication (JWT)

**Week 6: FAQ Generation & Integrations**
- [ ] Implement auto FAQ generation (LLM-based)
- [ ] Add FAQ approval workflow
- [ ] Create CSV export for FAQs
- [ ] Implement webhook integration
- [ ] Add CRM webhook support (Salesforce, HubSpot)
- [ ] Create lead capture in widget
- [ ] Add email notifications for missed questions

**v1 Acceptance Criteria:**
- [x] Can scrape 50+ pages reliably
- [x] Real-time voice conversations work smoothly
- [x] Admin can manage agents and view analytics
- [x] FAQs are auto-generated and can be edited
- [x] Webhooks fire on lead capture
- [x] System handles 100+ concurrent users

14.3 — v2 Scaling Phase (Month 2-4, 2-3 developers)

**Month 2: Multi-language & Multi-voice**
- [ ] Add language detection
- [ ] Implement multi-language embeddings
- [ ] Support multiple TTS voices per agent
- [ ] Add language-specific prompts
- [ ] Create voice selection UI
- [ ] Test with 5+ languages

**Month 3: Performance & Reliability**
- [ ] Implement on-device embedding fallback (small models)
- [ ] Add query result caching
- [ ] Optimize vector search (hybrid search with BM25)
- [ ] Implement connection pooling
- [ ] Add database read replicas
- [ ] Set up multi-region deployment
- [ ] Create SLA monitoring

**Month 4: Business Features**
- [ ] Implement billing system (Stripe)
- [ ] Add usage-based pricing tiers
- [ ] Create premium features (custom voices, analytics)
- [ ] Build customer portal
- [ ] Add team collaboration features
- [ ] Implement API rate limits per plan
- [ ] Create usage analytics for customers

**v2 Acceptance Criteria:**
- [x] Supports 10+ languages
- [x] P95 latency < 600ms for text queries
- [x] 99.9% uptime SLA
- [x] Multi-region deployment active
- [x] Billing and subscriptions working
- [x] 1000+ active agents supported

14.4 — Future Enhancements (v3+)

- [ ] Multi-modal support (images, PDFs)
- [ ] Custom knowledge base uploads
- [ ] Advanced analytics (sentiment, intent detection)
- [ ] A/B testing for prompts
- [ ] Custom model fine-tuning
- [ ] White-label widget options
- [ ] Mobile SDKs (iOS, Android)
- [ ] Voice cloning for customers
- [ ] Integration marketplace

⸻

15 — Security & Privacy Implementation

15.1 — Security Checklist

**Web Scraping Ethics:**
- [ ] Always respect robots.txt (parse and obey)
- [ ] Respect X-Robots-Tag HTTP headers
- [ ] Respect meta robots tags (noindex, nofollow)
- [ ] Implement configurable rate limiting (default: 1 req/sec)
- [ ] Use proper User-Agent identification
- [ ] Honor crawl-delay directives
- [ ] Provide admin override option (with warnings)

**Data Privacy:**
- [ ] Implement data retention policies (default: 90 days for conversations)
- [ ] Add user consent for audio recording
- [ ] Provide data deletion API endpoint
- [ ] Implement PII redaction option (emails, phones in transcripts)
- [ ] Add GDPR compliance features (right to access, deletion)
- [ ] Encrypt sensitive data at rest (database encryption)
- [ ] Use TLS 1.2+ for all communications

**Authentication & Authorization:**
- [ ] Implement JWT-based authentication
- [ ] Use short-lived tokens (24 hours default)
- [ ] Implement refresh token rotation
- [ ] Add API key authentication for widget
- [ ] Implement role-based access control (admin, user, viewer)
- [ ] Rate limit by API key/IP address
- [ ] Log all authentication attempts

**Input Validation:**
- [ ] Validate all URL inputs (prevent SSRF)
- [ ] Sanitize user queries (prevent injection)
- [ ] Validate file uploads (audio files)
- [ ] Implement request size limits
- [ ] Validate JSON schemas with Pydantic

**Code Security:**
- [ ] Use parameterized queries (prevent SQL injection)
- [ ] Escape output (prevent XSS)
- [ ] Implement CSP headers
- [ ] Regular dependency updates (Dependabot)
- [ ] Security scanning (Snyk, OWASP ZAP)
- [ ] Code review process

15.2 — Privacy Implementation

**Data Retention Policy:**
```python
# app/services/privacy.py
from datetime import datetime, timedelta

class PrivacyService:
    RETENTION_DAYS = 90
    
    async def delete_old_conversations(self):
        """Delete conversations older than retention period"""
        cutoff = datetime.utcnow() - timedelta(days=self.RETENTION_DAYS)
        # Delete from database
        # Delete audio files from S3
        pass
    
    async def redact_pii(self, text: str) -> str:
        """Redact PII from text"""
        # Redact emails
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        # Redact phones
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        return text
```

**GDPR Compliance:**
- Right to access: `GET /v1/users/{user_id}/data`
- Right to deletion: `DELETE /v1/users/{user_id}/data`
- Data portability: `GET /v1/users/{user_id}/export`

15.3 — Rate Limiting Implementation

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/v1/agents/{agent_id}/query")
@limiter.limit("100/minute")
async def query_agent(agent_id: str, request: Request):
    # Rate limited to 100 requests per minute per IP
    pass
```

15.4 — Security Headers

```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

⸻

16 — Acceptance criteria & KPIs
	•	Accuracy: >90% correct answers for scraped-fact questions (tested against 100 synthetic questions).
	•	Latency: text query < 600 ms (excluding TTS); end-to-end voice response < 3s for small answers.
	•	Uptime: 99% SLA for production.
	•	False hallucinates: <2% in closed test set (enforce with prompt + sources).

⸻

17 — Complete File Structure & Implementation Details

17.1 — Project Directory Structure

```
acorn/
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── Dockerfile.worker
├── .dockerignore
├── pyproject.toml
│
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Configuration management
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py        # Shared dependencies (DB, auth)
│   │   ├── middleware.py          # CORS, rate limiting, logging
│   │   │
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── onboard.py         # Agent creation & onboarding
│   │       ├── query.py           # Text query endpoint
│   │       ├── voice.py           # Voice query endpoint
│   │       ├── websocket.py       # WebSocket real-time endpoint
│   │       ├── admin.py           # Admin dashboard API
│   │       └── health.py         # Health check endpoints
│   │
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── scraper_worker.py      # Main scraping worker
│   │   ├── indexer_worker.py      # Embedding & indexing worker
│   │   └── queue.py               # Job queue (Redis/RQ or Celery)
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── scraper.py             # Playwright scraping logic
│   │   ├── extractor.py           # Structured data extraction
│   │   ├── chunker.py             # Smart chunking algorithm
│   │   ├── indexer.py             # Vector DB operations
│   │   ├── rag.py                 # RAG query pipeline
│   │   ├── stt_tts.py             # Speech-to-text & text-to-speech
│   │   ├── llm.py                 # LLM client wrapper
│   │   ├── embeddings.py          # Embedding generation
│   │   └── summarizer.py          # LLM summarization & FAQ generation
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schemas.py             # Pydantic models
│   │   ├── database.py            # SQLAlchemy models
│   │   └── db.py                  # Database connection & session
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── text_processing.py     # Text cleaning, normalization
│   │   ├── validators.py          # URL validation, etc.
│   │   └── security.py            # JWT, encryption
│   │
│   └── tests/
│       ├── __init__.py
│       ├── test_scraper.py
│       ├── test_chunker.py
│       ├── test_rag.py
│       ├── test_api.py
│       └── fixtures/
│
├── frontend/
│   ├── widget/
│   │   ├── agent-widget.js        # Embeddable widget (vanilla JS)
│   │   ├── widget.css
│   │   └── widget.html            # Example usage
│   │
│   └── admin/
│       ├── package.json
│       ├── src/
│       │   ├── App.jsx
│       │   ├── components/
│       │   │   ├── AgentList.jsx
│       │   │   ├── ScrapeLogs.jsx
│       │   │   ├── Analytics.jsx
│       │   │   └── FAQEditor.jsx
│       │   └── api/
│       └── public/
│
├── scripts/
│   ├── init_db.py                 # Database initialization
│   ├── migrate.py                # Database migrations
│   └── seed_data.py              # Seed test data
│
└── docs/
    ├── api.md                     # API documentation
    ├── deployment.md             # Deployment guide
    └── architecture.md            # Architecture diagrams
```

17.2 — Complete API Endpoint Specifications

**POST /v1/onboard**
Create a new agent and start scraping job.

Request:
```json
{
  "root_url": "https://example.com",
  "name": "Example Business",
  "config": {
    "voice": {"provider": "elevenlabs"},
    "scraping": {"max_pages": 50}
  }
}
```

Response:
```json
{
  "agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "embed_code": "<script src='https://cdn.example.com/widget.js' data-agent='550e8400-e29b-41d4-a716-446655440000' async></script>",
  "public_key": "pk_live_abc123..."
}
```

**GET /v1/agents/{agent_id}/status**
Get agent scraping status.

Response:
```json
{
  "agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "ready",
  "last_scraped": "2024-01-15T10:30:00Z",
  "pages_scraped": 42,
  "total_chunks": 156
}
```

**POST /v1/agents/{agent_id}/query**
Text query endpoint.

Request:
```json
{
  "query": "What are your opening hours?",
  "session_id": "session_123",
  "include_sources": true
}
```

Response:
```json
{
  "answer": "We're open Monday to Friday, 9 AM to 5 PM.",
  "sources": [
    {
      "chunk_id": "chunk_abc",
      "url": "https://example.com/contact",
      "relevance_score": 0.92
    }
  ],
  "latency_ms": 450
}
```

**POST /v1/agents/{agent_id}/voice**
Voice query (multipart audio upload).

Request: multipart/form-data
- `audio`: audio file (wav, mp3, m4a)
- `session_id`: string (optional)

Response:
```json
{
  "transcript": "What are your opening hours?",
  "answer": "We're open Monday to Friday, 9 AM to 5 PM.",
  "audio_url": "https://cdn.example.com/audio/response_123.mp3",
  "sources": [...]
}
```

**WebSocket /v1/realtime/{agent_id}**
Bi-directional streaming for real-time voice.

Connection: `wss://api.example.com/v1/realtime/{agent_id}?key=EPHEMERAL_KEY`

Messages:
- Client → Server: `{"type": "audio_chunk", "data": "base64_audio"}`
- Server → Client: `{"type": "transcript", "text": "..."}`
- Server → Client: `{"type": "audio_chunk", "data": "base64_audio"}`
- Server → Client: `{"type": "done"}`

**GET /v1/admin/agents**
List all agents (admin only).

**GET /v1/admin/agents/{agent_id}/scrape-logs**
Get scraping job logs.

**PUT /v1/admin/faqs/{faq_id}**
Edit/approve FAQ answer.

**GET /v1/admin/analytics/{agent_id}**
Get analytics data.

17.3 — Core Service Implementation Examples

**app/services/chunker.py** (Smart Chunking)
```python
from typing import List, Dict
import tiktoken
from app.models.schemas import Chunk

class SmartChunker:
    def __init__(self, min_tokens=400, max_tokens=700, overlap_tokens=50):
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def chunk_by_sections(self, text: str, headers: List[Dict]) -> List[Chunk]:
        """Chunk text by semantic sections (headers)"""
        # Implementation: group by headers, respect token limits
        pass
    
    def compute_importance(self, chunk: str, metadata: Dict) -> float:
        """Compute importance score based on content"""
        score = 0.0
        # Boost for contact info, prices, headers
        if any(keyword in chunk.lower() for keyword in ['phone', 'email', 'contact']):
            score += 0.3
        if '$' in chunk or '£' in chunk or '€' in chunk:
            score += 0.2
        if metadata.get('header_level') == 1:
            score += 0.3
        return min(score, 1.0)
```

**app/services/indexer.py** (Vector DB Operations)
```python
from pinecone import Pinecone, ServerlessSpec
from app.config import settings

class VectorIndexer:
    def __init__(self):
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index = self.pc.Index(settings.PINECONE_INDEX_NAME)
    
    def upsert_chunks(self, agent_id: str, chunks: List[Dict]):
        """Batch upsert chunks to Pinecone"""
        vectors = []
        for chunk in chunks:
            vectors.append({
                "id": chunk['chunk_id'],
                "values": chunk['embedding'],
                "metadata": {
                    "agent_id": agent_id,
                    "url": chunk['url'],
                    "category": chunk.get('category'),
                    "importance": chunk.get('importance_score', 0.0)
                }
            })
        self.index.upsert(vectors=vectors, namespace=agent_id)
```

**app/services/rag.py** (RAG Query Pipeline)
```python
from app.services.indexer import VectorIndexer
from app.services.llm import LLMClient
from app.services.embeddings import EmbeddingService

class RAGService:
    def __init__(self):
        self.indexer = VectorIndexer()
        self.llm = LLMClient()
        self.embeddings = EmbeddingService()
    
    async def query(self, agent_id: str, query: str, top_k: int = 8) -> Dict:
        # 1. Generate query embedding
        query_embedding = await self.embeddings.embed(query)
        
        # 2. Vector search
        results = self.indexer.index.query(
            vector=query_embedding,
            top_k=top_k,
            namespace=agent_id,
            include_metadata=True
        )
        
        # 3. Build context from chunks
        context = "\n\n".join([r.metadata['content'] for r in results.matches])
        
        # 4. LLM call with context
        answer = await self.llm.generate(
            system_prompt=self._build_system_prompt(agent_id),
            user_prompt=f"Context:\n{context}\n\nQuestion: {query}",
            temperature=0.1
        )
        
        return {
            "answer": answer,
            "sources": [{"chunk_id": r.id, "url": r.metadata['url']} for r in results.matches]
        }
```

17.4 — Environment Variables (.env.example)

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/acorn
DATABASE_POOL_SIZE=10

# Vector DB
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=acorn-index
PINECONE_ENVIRONMENT=us-east-1

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-large

# TTS/STT
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
OPENAI_WHISPER_MODEL=whisper-1

# Redis (for job queue)
REDIS_URL=redis://localhost:6379/0

# Security
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Storage (S3 or local)
STORAGE_TYPE=s3
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET=acorn-storage
STORAGE_BASE_URL=https://cdn.example.com

# Monitoring
SENTRY_DSN=...
LOG_LEVEL=INFO

# Feature flags
ENABLE_WEBSOCKET=true
ENABLE_ADMIN_DASHBOARD=true
MAX_PAGES_PER_SCRAPE=50
```

17.5 — Docker Configuration

**Dockerfile** (API Service)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Dockerfile.worker** (Scraper Worker)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Playwright and dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

COPY app/ ./app/

CMD ["python", "-m", "app.workers.scraper_worker"]
```

**docker-compose.yml**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: acorn
      POSTGRES_USER: acorn
      POSTGRES_PASSWORD: acorn_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://acorn:acorn_dev@postgres:5432/acorn
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      DATABASE_URL: postgresql://acorn:acorn_dev@postgres:5432/acorn
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
```

⸻

18 — 5-hour sprint (practical checklist)

If you want a demo in ~5 hours (as we agreed earlier), do this sprint:

Hour 0.5 — Setup repo, Docker, basic FastAPI, onboarding page
Hour 1.5 — Implement single-page scraper (Playwright) + cleaning
Hour 2.5 — Smart chunker + generate embeddings (use OpenAI) + upsert to Pinecone
Hour 3.5 — Basic RAG endpoint (query → vector search → prompt → OpenAI)
Hour 4.0 — Minimal widget that uploads audio file (or text) to /query
Hour 5.0 — Test on dummy site, fix bugs, deploy to Railway

Deliverable: working demo that scrapes 1 page, indexes it, and answers voice/text queries.

⸻

19 — Next actions (pick one)
	•	I can generate the full Python codebase (scraper, chunker, indexer, RAG API, widget).
	•	Or I can produce just the scraper + chunker + JSON output you can run locally.
	•	Or produce the 5-hour sprint checklist with exact commands and starter repo (Dockerfile, requirements, GH Actions).

Tell me which of the three you want and I'll produce the artifacts immediately (Python code files, or a zipped repo).

⸻

20 — Quick Start Guide

20.1 — Local Development Setup

**Prerequisites:**
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

**Step 1: Clone and Setup**
```bash
git clone <repo-url>
cd acorn
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Step 2: Environment Configuration**
```bash
cp .env.example .env
# Edit .env with your API keys:
# - OPENAI_API_KEY
# - PINECONE_API_KEY
# - DATABASE_URL
# - REDIS_URL
```

**Step 3: Database Setup**
```bash
# Initialize database
python scripts/init_db.py

# Run migrations
alembic upgrade head
```

**Step 4: Start Services**
```bash
# Option A: Docker Compose (recommended)
docker-compose up -d

# Option B: Manual
# Terminal 1: API
uvicorn app.main:app --reload --port 8000

# Terminal 2: Worker
python -m app.workers.scraper_worker

# Terminal 3: Redis (if not using Docker)
redis-server
```

**Step 5: Test the API**
```bash
# Health check
curl http://localhost:8000/healthz

# Create an agent
curl -X POST http://localhost:8000/v1/onboard \
  -H "Content-Type: application/json" \
  -d '{"root_url": "https://example.com", "name": "Test"}'

# Query the agent (after scraping completes)
curl -X POST http://localhost:8000/v1/agents/{agent_id}/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this website about?"}'
```

20.2 — Production Deployment Checklist

**Pre-deployment:**
- [ ] All environment variables set
- [ ] Database migrations applied
- [ ] SSL certificates configured
- [ ] Domain DNS configured
- [ ] Monitoring and alerts set up
- [ ] Backup strategy in place
- [ ] Security scan completed
- [ ] Load testing completed
- [ ] Documentation updated

**Deployment:**
- [ ] Build Docker images
- [ ] Push to container registry
- [ ] Deploy to production environment
- [ ] Run health checks
- [ ] Monitor error rates
- [ ] Verify all services running

**Post-deployment:**
- [ ] Smoke tests passed
- [ ] Performance metrics normal
- [ ] No critical errors in logs
- [ ] Team notified of deployment

20.3 — Common Issues & Troubleshooting

**Issue: Scraper fails on JavaScript sites**
- Solution: Ensure Playwright is installed: `playwright install chromium`

**Issue: Vector search returns no results**
- Check: Pinecone index exists and has data
- Check: Namespace matches agent_id
- Check: Embeddings are being generated correctly

**Issue: High latency on queries**
- Check: Database connection pool size
- Check: Vector DB region (should be close to API)
- Check: LLM API rate limits
- Consider: Adding caching layer

**Issue: Audio quality issues**
- Check: TTS provider API limits
- Check: Audio encoding settings
- Consider: Using different TTS provider

⸻

21 — Additional Resources

**Documentation:**
- FastAPI: https://fastapi.tiangolo.com/
- Playwright: https://playwright.dev/python/
- Pinecone: https://docs.pinecone.io/
- OpenAI: https://platform.openai.com/docs/

**Example Implementations:**
- LangChain RAG: https://python.langchain.com/docs/use_cases/question_answering/
- Vector DB best practices: https://www.pinecone.io/learn/vector-database/

**Community:**
- Discord/Slack channel for support
- GitHub Discussions for questions
- Blog posts on implementation details

**Support:**
- Email: support@example.com
- Documentation: https://docs.example.com
- Status page: https://status.example.com