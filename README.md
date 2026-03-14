# ARIA — Autonomous Research Intelligence Agent

**AI-powered research assistant that crawls academic papers, extracts claims, builds knowledge graphs, and generates synthesis reports.**

> 🔬 ARIA acts as a junior researcher that never sleeps — you give it a question, it delivers a literature review.

---

## 🆓 100% Free Stack

| Component | Solution | Limit |
|-----------|----------|-------|
| LLM (reasoning, extraction, synthesis) | Gemini 1.5 Flash | 15 req/min, 1M tokens/day |
| Embeddings | sentence-transformers (local) | Unlimited |
| Paper search | arXiv API | Unlimited |
| Paper citations | Semantic Scholar | 100 req/5min |
| Biomedical papers | PubMed NCBI | 3 req/sec |
| Vector search | ChromaDB (local) | Unlimited |
| Knowledge graph | NetworkX (in-memory) | Unlimited |

---

## ⚡ Quick Start (3 Commands)

### Prerequisites
- Python 3.11+
- Node.js 18+
- A free Gemini API key from [ai.google.dev](https://ai.google.dev)

### 1. Backend

```bash
cd aria/backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 2. Run Backend

```bash
cd aria/backend
uvicorn main:app --reload --port 8000
```

### 3. Run Frontend (new terminal)

```bash
cd aria/frontend
npm install
npm run dev
```

Open http://localhost:5173 and ask ARIA a research question!

---

## 🧠 What ARIA Does

1. **Accept a research question** as natural language
2. **Crawl** arXiv + Semantic Scholar + PubMed simultaneously
3. **Follow citation trails** 2 levels deep
4. **Extract** claims, methodology, results, and limitations using Gemini Flash
5. **Build a Knowledge Graph** with support/contradiction/citation edges
6. **Generate 3 structured outputs:**
   - 📄 **Literature Summary** (grouped by theme)
   - ⚠️ **Contradiction Report** (conflicting findings)
   - 🔍 **Research Gap Brief** (unanswered questions)
7. **Conversational Q&A** — ask follow-up questions across all papers

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/research` | Start a new research session |
| GET | `/api/status/{session_id}` | SSE stream of real-time progress |
| GET | `/api/results/{session_id}` | Get completed research results |
| POST | `/api/query` | Ask a follow-up question |
| GET | `/api/graph/{session_id}` | Get knowledge graph data |
| GET | `/api/graph/{session_id}/stats` | Get graph statistics |

### Example: Start Research

```bash
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{"question": "How do large language models handle hallucination?", "max_papers": 30, "depth": 2}'
```

---

## 📁 Project Structure

```
aria/
├── backend/
│   ├── main.py                  # FastAPI entry point
│   ├── llm_client.py            # Gemini 1.5 Flash client
│   ├── embeddings_client.py     # sentence-transformers (local)
│   ├── agents/
│   │   ├── orchestrator.py      # Pipeline coordinator
│   │   ├── crawler_agent.py     # Multi-source paper crawler
│   │   ├── extractor_agent.py   # Structured extraction via Gemini
│   │   ├── graph_agent.py       # Knowledge graph builder
│   │   ├── synthesis_agent.py   # Output generator
│   │   └── conversational_agent.py  # Q&A agent
│   ├── tools/
│   │   ├── arxiv_tool.py        # arXiv search
│   │   ├── semantic_scholar_tool.py  # Semantic Scholar search + citations
│   │   ├── pubmed_tool.py       # PubMed/NCBI search
│   │   └── pdf_reader_tool.py   # PDF text extraction
│   ├── graph/
│   │   ├── knowledge_graph.py   # NetworkX knowledge graph
│   │   └── graph_export.py      # Export utilities
│   ├── vector/
│   │   └── chroma_store.py      # ChromaDB vector store
│   ├── models/                  # Pydantic data models
│   └── api/                     # FastAPI route modules
│
└── frontend/
    ├── src/
    │   ├── App.jsx              # Root component
    │   ├── store/useAriaStore.js # Zustand state
    │   ├── components/          # 8 React components
    │   └── pages/               # HomePage + ResultsPage
    └── ...config files
```

---

## 🔑 Environment Variables

```env
GEMINI_API_KEY=your_free_key_here
```

That's it. Everything else is free with no API key required.

---

## License

MIT
