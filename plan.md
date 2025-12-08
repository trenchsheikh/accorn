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

Agent record (Postgres)

agents(
  id uuid primary key,
  owner_id uuid,
  domain text,
  root_url text,
  created_at timestamptz,
  last_scraped timestamptz,
  status text, -- pending / ready / failed
  config jsonb -- voice, personality, settings
)

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

11 — Deployment & infra
	•	Dockerize services (scraper-worker, api, indexer, admin).
	•	Use managed Postgres, Pinecone, S3 for logs/artifacts.
	•	For audio streaming, ensure low-latency server colocated near clients (or use CDN).
	•	Secrets: store in vault (Railway/GitHub Secrets/AWS Secrets Manager).

Cost (rough):
	•	Pinecone small: ~$50–200/mo (depends on volumes)
	•	OpenAI usage: depends on token usage — budget per 10k queries.
	•	Hosting (small): $50–200/mo for MVP.
	•	Playwright rendering increases CPU costs.

⸻

12 — Testing plan
	•	Unit tests for chunker + extractor.
	•	Integration test: run scraper against sample sites (3 types: static site, JS site, ecommerce).
	•	Load test: simulate 100 concurrent widget users.
	•	Security test: ensure no secret leak via widget, rate-limit abuse.

⸻

13 — Monitoring & ops
	•	Health endpoints /healthz for each service.
	•	Job metrics: scrape success/failure rates, average time, pages per job.
	•	Conversation metrics: average latency, TTS latency, STT latency.
	•	Alerts on high error rates or excessive cost usage.

⸻

14 — Roadmap & milestones (prioritised)

MVP (1 developer, ~5–12 days depending on polish)
	•	Onboarding UI (paste URL, start job).
	•	Scraper worker (Playwright, same-domain, depth=1–2, max pages 10).
	•	Chunker + embed + index to Pinecone.
	•	RAG endpoint for text queries + simple widget for voice (record→upload).
	•	TTS output file (non-streaming).
Acceptance: create agent from https://example-business, embed on dummy site, ask queries, answers accurate from scraped content.

v1 (productionize, 2–4 weeks)
	•	Deep crawling (depth=3, max 50 pages) + dedupe + retries.
	•	Streaming WebSocket voice (real-time).
	•	Admin dashboard + manual edit of answers.
	•	FAQ autogen & CSV export.
	•	Integrations (CRM, webhooks).

v2 (scaling & features, 1–3 months)
	•	Multi-voice, multi-language.
	•	On-device fallback small embeddings.
	•	SLAs, multi-region deployment.
	•	Pricing, billing, premium features (custom voices, analytics).

⸻

15 — Security & privacy checklist
	•	Obey robots.txt by default; admin override option.
	•	Respect Do Not Index meta tags.
	•	Data retention policy and user consent for recording.
	•	Option to redact PII from transcripts.
	•	Encrypt data at rest + in transit.

⸻

16 — Acceptance criteria & KPIs
	•	Accuracy: >90% correct answers for scraped-fact questions (tested against 100 synthetic questions).
	•	Latency: text query < 600 ms (excluding TTS); end-to-end voice response < 3s for small answers.
	•	Uptime: 99% SLA for production.
	•	False hallucinates: <2% in closed test set (enforce with prompt + sources).

⸻

17 — Example code skeleton (FastAPI + Playwright + Pinecone)

File layout

/app
  /workers
    scraper_worker.py
  /api
    main.py
    routes/query.py
    routes/onboard.py
  /services
    chunker.py
    extractor.py
    indexer.py
    stt_tts.py
  /models
    schemas.py
  Dockerfile
  requirements.txt

Sample FastAPI endpoint (sketch)

# app/api/routes/onboard.py
from fastapi import APIRouter
from uuid import uuid4
router = APIRouter()

@router.post("/onboard")
async def onboard(payload: dict):
    agent_id = str(uuid4())
    # enqueue job with root_url, agent_id
    return {"agent_id": agent_id, "embed": f"<script src='...agent.js' data-agent='{agent_id}'></script>"}

I can produce fully working code files on request (scraper, chunker, indexer, FastAPI) — say the word and I’ll generate them.

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

Tell me which of the three you want and I’ll produce the artifacts immediately (Python code files, or a zipped repo).