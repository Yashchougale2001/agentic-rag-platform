````markdown
# Agentic RAG Chatbot

An **agentic RAG** (Retrieval-Augmented Generation) chatbot for **HR & IT asset data**, built with:

- **LangGraph** for multi-step agent orchestration
- **Groq LLM** (primary, via `GROQ_API_KEY`) with fallback to **TinyLLaMA** via **Ollama**
- **BAAI/bge-small-en-v1.5** embeddings (local, via `sentence-transformers`)
- **ChromaDB** as a local persistent vector store
- **Agentic tools** for:
  - Knowledge-base retrieval (Chroma)
  - Local directory search (filesystem)
  - Conversation + user memory
  - RBAC / permission filtering
  - Feedback logging for evaluation
- REST API (FastAPI) + CLI entrypoints

> Note: PII detection/redaction components exist but are **not wired into the default ingestion pipeline**. All ingested text is stored and embedded as-is unless you explicitly enable PII processing.

The chatbot is designed to be:

- Modular (swappable LLMs, embedders, and vector stores)
- Agentic (LangGraph-based planner + tools)
- Focused on HR policies and IT assets
- Able to ingest local & remote files
- Exposed via both CLI and REST API

---

## Project Structure

```text
your_project/
│
├── config/
│   ├── __init__.py
│   ├── settings.yaml       # env, LLM provider priority, logging, retrieval params
│   ├── model.yaml          # LLM & embedding model names + retrieval config
│   └── paths.yaml          # data, db, logs, tmp directories
│
├── data/                   # your HR/IT data (e.g., data/hr_policies, data/it_assets, data/hr_local)
│
├── src/
│   ├── __init__.py
│   ├── ingestion/          # loaders & ingestion pipeline
│   │   ├── __init__.py
│   │   ├── csv_loader.py
│   │   ├── yaml_loader.py
│   │   ├── text_loader.py
│   │   ├── md_loader.py
│   │   ├── xlsx_loader.py
│   │   ├── json_loader.py
│   │   └── ingest_pipeline.py
│   │
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── pii_detector.py
│   │   ├── pii_redactor.py
│   │   ├── query_rewriter.py
│   │   └── chunker.py           # document chunking
│   │
│   ├── embeddings/              # BGE embeddings
│   │   ├── __init__.py
│   │   ├── bge_model.py
│   │   └── embedder.py
│   │
│   ├── db/                      # ChromaDB client & vector store wrapper
│   │   ├── __init__.py
│   │   ├── chroma_client.py
│   │   ├── bm25_store.py
│   │   ├── hybrid_retrieval.py
│   │   └── vector_store.py
│   │
│   ├── retrieval/               # High-level retriever(s)
│   │   ├── __init__.py
│   │   ├── reranker.py
│   │   └── retriever.py         # dense / hybrid / lexical retrieval
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── ollama_client.py
│   │   ├── chroma_model.py      # placeholder for future models
│   │   └── generator.py         # LLMGenerator (Groq + Ollama TinyLLaMA)
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── agent_core.py        # (legacy core RAG agent, optional)
│   │   ├── graph_agent.py       # LangGraph agent wiring (advanced agent)
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── knowledge_base_tool.py   # wraps Retriever (Chroma/BM25/hybrid)
│   │       ├── local_directory_tool.py  # keyword search in local filesystem
│   │       ├── memory_tool.py           # conversation + user profile memory
│   │       ├── rbac_tool.py             # RBAC / permission filtering
│   │       └── feedback_tool.py         # feedback logging for evaluation
│   │
│   └── utils/
│       ├── __init__.py
│       ├── config_loader.py
│       ├── file_utils.py
│       └── logging_config.py    # central logging setup
│
├── cli/
│   ├── __init__.py
│   ├── main.py                  # simple CLI chatbot (legacy/core agent)
│   ├── ingest.py                # CLI ingestion (file/folder/url)
│   └── langgraph_agent_main.py  # CLI using LangGraph agent (with memory + RBAC)
│
├── api/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app entrypoint
│   └── routes/
│       ├── __init__.py
│       ├── query.py             # /query endpoint (LangGraph agent)
│       ├── ingest.py            # /ingest/file, /ingest/url, /ingest/folder
│       └── feedback.py          # /feedback endpoint (optional)
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Mini Architecture Flow Diagram

User → Planner → Tool (KB/Local) → RBAC Filter → LLM → Memory Save → Response

## Features

### 1. Advanced Agentic RAG

The LangGraph agent (in `src/agent/graph_agent.py`) orchestrates multiple tools:

- **Knowledge base retrieval** (Chroma/BGE, with optional BM25/hybrid):
  - Via `Retriever` (`src/retrieval/retriever.py`) wrapped by `KnowledgeBaseTool`.
- **Local directory search**:
  - Via `LocalDirectoryTool`, scanning a configurable folder (default: `data/hr_local`).
- **LLM-based planner**:
  - Decides between:
    - `KB_SEARCH` – query the vector store
    - `LOCAL_SEARCH` – search the local filesystem
    - `ANSWER` – answer from existing context + memory
- **RBAC enforcement**:
  - `RBACFilterTool` filters docs based on:
    - `role` (`admin`, `hr`, `employee`)
    - document `metadata.visibility` and `metadata.owner_user_id`
- **Conversation + user memory**:
  - `MemoryTool` stores:
    - recent Q&A turns per `user_id`
    - a simple user profile per `user_id`

### 2. RAG-based HR/IT Q&A

- Answers are grounded in **ingested HR/IT datasets** (no arbitrary outside knowledge).
- Uses **BGE-Small** (`BAAI/bge-small-en-v1.5`) embeddings + **ChromaDB**.
- Supports dense, lexical, or hybrid retrieval via `retriever.py`.
- Recency and reranking (optional) can be configured via `model.yaml`.

### 3. Orchestrated LLM Usage

`LLMGenerator` (`src/llm/generator.py`):

- Chooses provider by priority:
  - **Groq** (`GROQ_API_KEY` required); default model `llama-3.3-70b-versatile`.
  - Fallback to local **TinyLLaMA** via **Ollama**.
- Used in:
  - Query rewriting (if enabled)
  - The main RAG answer generation
  - The planner node (to choose next action)

The system prompts are tuned for **IT/HR assets and policy**-style questions.

### 4. Flexible Ingestion

Ingestion pipeline (`src/ingestion/ingest_pipeline.py`) supports:

- Files:
  - CSV
  - XLSX/XLS
  - JSON
  - TXT
  - MD
  - YAML
  - PDF
  - DOC/DOCX
- Folders:
  - Recursively ingest all supported files in a directory.
- URLs:
  - Download and process remote files.

Documents are chunked and embedded, then stored in ChromaDB.

### 5. APIs & Tools

**REST API (FastAPI)**:

- `POST /query` – ask questions via LangGraph agent  
  Request body:

  ```json
  {
    "question": "What is the laptop replacement policy?",
    "user_id": "emp_123",
    "role": "employee"
  }
  ```

  Response shape:

  ```json
  {
    "answer": "Employees are eligible for a laptop replacement every 3 years...",
    "steps": [
      "load_memory",
      "plan:KB_SEARCH",
      "kb_retrieve",
      "plan:ANSWER",
      "generate_answer",
      "save_memory"
    ],
    "context_sources": ["data/hr_policies/laptop_policy.md"]
  }
  ```

- `POST /ingest/file` – upload a file to ingest.
- `POST /ingest/url` – ingest from a remote URL.
- `POST /ingest/folder` – ingest all files in a local folder (server-side path).
- `POST /feedback` (optional) – submit user feedback:

  ```json
  {
    "user_id": "emp_123",
    "role": "employee",
    "question": "What is the laptop replacement policy?",
    "answer": "...",
    "rating": 1,
    "comment": "Correct and clear.",
    "context_sources": ["data/hr_policies/laptop_policy.md"]
  }
  ```

  Feedback entries are appended to `logs/feedback.jsonl` for offline evaluation.

**CLI**:

- `cli/main.py` – simple core chatbot (using legacy agent, optional).
- `cli/langgraph_agent_main.py` – CLI using the **LangGraph agent** (planner + memory + RBAC).
- `cli/ingest.py` – ingest file/folder/URL from the command line.

The LangGraph CLI mirrors the API:

- It uses the same compiled graph.
- It asks for (or takes as args) `user_id` and `role`.
- It returns and displays `answer`, `steps`, and `context_sources`.

### 6. Logging

Centralized logging via `src/utils/logging_config.py`:

- Logs to console.
- Logs to a file under `logs/` (default: `logs/app.log`, configurable in `config/settings.yaml`):

  ```yaml
  logging:
    level: INFO
    file: logs/app.log
  ```

Directories for logs, DB, and temp files come from `config/paths.yaml`.

---

## Setup

```bash
git clone <this-repo>
cd your_project
python -m venv .venv
```

Activate the virtual environment:

- On **Windows (PowerShell)**:

  ```bash
  .\.venv\Scripts\Activate.ps1
  ```

- On **Linux/macOS**:

  ```bash
  source .venv/bin/activate
  ```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Configuration

### Environment variables

#### Groq (optional but recommended)

To use Groq as the primary LLM:

- Install `groq` (should already be in `requirements.txt`).
- Set `GROQ_API_KEY`:

**PowerShell:**

```powershell
$env:GROQ_API_KEY = "sk_your_real_key_here"
```

**cmd:**

```cmd
set GROQ_API_KEY=sk_your_real_key_here
```

#### Ollama (for TinyLLaMA fallback)

- Install and run **Ollama**.
- Pull the TinyLLaMA model:

```bash
ollama pull tinyllama
```

### Paths and logging

`config/paths.yaml`:

```yaml
paths:
  base_dir: "."
  data_dir: "data"
  db_dir: "data/chroma_db"
  logs_dir: "logs"
  tmp_dir: "data/tmp"
```

`config/settings.yaml` (example):

```yaml
env: "dev"

logging:
  level: INFO
  file: logs/app.log

llm:
  provider_priority:
    - "groq"
    - "ollama"
  max_tokens: 512
  temperature: 0.1

retrieval:
  top_k: 5
  min_relevance_score: 0.2

security:
  enable_pii_redaction: false # PII detection not active by default

monitoring:
  log_queries: true
  log_ingestions: true
  log_file: "logs/app.log"
```

---

## Running the API

From the project root:

```bash
uvicorn api.main:app --reload --port 8000
```

Key endpoints:

- `POST /query` – main chat endpoint (LangGraph agent).
- `POST /ingest/file` – ingest a single file.
- `POST /ingest/url` – ingest from URL.
- `POST /ingest/folder` – ingest all supported files in a folder.
- `POST /feedback` – submit feedback on answers.

Interactive docs:

- Swagger UI: `http://127.0.0.1:8000/docs`

---

## CLI Usage

### LangGraph Agent CLI (recommended)

```bash
python -m cli.main
```

You’ll be prompted for a role if not specified and a default `user_id` (`cli_user`) will be used.

Single-query example:

```bash
python -m cli.langgraph_agent_main \
  --query "What is the laptop replacement policy?" \
  --user-id emp_123 \
  --role employee
```

### Ingestion (CLI)

```bash
# Ingest a single file into hr_policies dataset
python -m cli.ingest --path path/to/hr_policies.pdf --dataset hr_policies

# Ingest an entire folder (recursively)
python -m cli.ingest --path data/hr_policies --dataset hr_policies

# Another dataset (e.g., IT assets)
python -m cli.ingest --path data/it_assets --dataset it_assets

# Ingest from a URL
python -m cli.ingest --path https://example.com/hr_policy.pdf --dataset hr_policies
```

---

## Notes

- **PII**: Detection/redaction modules exist (`pii_detector.py`, `pii_redactor.py`) but are not active by default in the ingestion pipeline.
- **RBAC**: To fully leverage RBAC, ensure your ingested documents carry useful `metadata`, such as:
  - `visibility`: `"public" | "hr" | "admin" | "private"`
  - `owner_user_id`: for employee-specific documents.
    RBAC filtering occurs after retrieval and before answer generation, ensuring the LLM never sees unauthorized content.
- **Memory**: Conversation history and user profiles are stored under `data/memory/` and used to provide more contextual, personalized answers.
- **Planner**: The LLM-based planner can be tuned (prompt editing) to match your operational preferences for when to use KB vs local search vs direct answering.

You can further customize retrieval, prompts, tools, and metadata to better match your HR/IT data model and internal policies.
````
