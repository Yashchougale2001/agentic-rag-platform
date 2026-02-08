Here is an updated, cleaned-up `README.md` that matches your current codebase and removes the outdated PII references, corrects paths, and formats everything properly.

````markdown
# Agentic RAG Chatbot

An **agentic RAG** (Retrieval-Augmented Generation) chatbot for **HR data & policies**, built with:

- **LangGraph** for agent orchestration
- **Groq LLM** (primary, via `GROQ_API_KEY`) with fallback to **TinyLLaMA** via **Ollama**
- **BAAI/bge-small-en-v1.5** embeddings (local, via `sentence-transformers`)
- **ChromaDB** as a local persistent vector store
- Flexible ingestion of local and remote datasets (CSV, TXT, MD, PDF, DOCX, YAML)
- REST API (FastAPI) + CLI entrypoints

> Note: PII detection/redaction is **disabled** in the current version. All ingested text is stored and embedded as-is.

It’s designed to be:

- Modular (you can swap LLMs/embedders/vector stores later)
- Agentic (LangGraph-based RAG agent)
- HR-policy-focused
- Able to ingest local & remote files
- Exposed through both CLI and REST API (FastAPI)

---

## Project Structure

```text
hr_chatbot/
│
├── config/
│   ├── __init__.py
│   ├── settings.yaml       # env, LLM provider priority, logging, retrieval params
│   ├── model.yaml          # LLM & embedding model names
│   └── paths.yaml          # data, db, logs, tmp directories
│
├── data/                   # your HR data (e.g., data/hr_policies, data/hr_data)
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
│   │   ├── hybrid_retrival.py
│   │   └── vector_store.py
│   │
│   ├── retrieval/               # Retriever
│   │   ├── __init__.py
│   │   ├── reranker.py
│   │   └── retriever.py
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── ollama_client.py
│   │   ├── chroma_model.py      # placeholder for future models
│   │   └── generator.py         # LLMGenerator (Groq + Ollama TinyLLaMA)
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── agent_core.py        # HRRAGAgentCore (retrieve + generate)
│   │   ├── graph_agent.py       # LangGraph agent wiring
│   │   └── agent_tools/
│   │       ├── __init__.py
│   │       ├── rag_tool.py
│   │       ├── email_tool.py
│   │       ├── local_search_tool.py
│   │       └── analyze_asset.py # placeholder for future HR automation
│   │
│   └── utils/
│       ├── __init__.py
│       ├── config_loader.py
│       ├── file_utils.py
│       └── logging_config.py    # central logging setup
│
├── cli/
│   ├── __init__.py
│   ├── main.py                  # CLI chatbot (core agent)
│   ├── ingest.py                # CLI ingestion (file/folder/url)
│   └── langgraph_agent_main.py  # CLI using LangGraph agent
│
├── api/                         # FastAPI app
│   ├── __init__.py
│   ├── main.py                  # app entrypoint
│   └── routes/
│       ├── __init__.py
│       ├── query.py             # /query endpoint
│       └── ingest.py            # /ingest/file, /ingest/url, /ingest/folder
│
├── requirements.txt
├── README.md
└── .gitignore
```
````

---

## Features

### RAG-based HR Q&A

- Answers only from ingested HR datasets (no outside knowledge).
- Uses BGE-Small (`BAAI/bge-small-en-v1.5`) embeddings + ChromaDB for retrieval.
- Documents are chunked for efficient and accurate retrieval.

### LLM Orchestration

- `LLMGenerator` chooses:
  - **Groq** first (if `GROQ_API_KEY` is available and Groq client initializes),
  - Then **TinyLLaMA via Ollama** as a fallback.
- System prompt tuned for **HR policies**.
- Final answers are **plain text only**:
  - No citations
  - No `[1]`/`[2]` markers
  - No `[source: ...]` or file paths exposed

### Flexible Ingestion

Local & remote ingestion of:

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
  - Recursively ingest all supported files in a directory
- URLs:
  - Download remote file then run full ingestion pipeline

### APIs & Tools

**REST API (FastAPI)**:

- `POST /query` – ask questions
- `POST /ingest/file` – upload a file
- `POST /ingest/url` – ingest from URL
- `POST /ingest/folder` – ingest all files in a local folder (server-side path)

**CLI**:

- `cli/main.py` – simple HR chatbot (core agent)
- `cli/langgraph_agent_main.py` – chatbot using LangGraph agent
- `cli/ingest.py` – ingest file/folder/URL from the command line

### Logging

Centralized logging configuration via `src/utils/logging_config.py`:

- Logs to console
- And to a file under `logs/` (default: `logs/app.log`, configurable in `config/settings.yaml`)

---

## Setup

```bash
git clone <this-repo>
cd hr_chatbot
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

### Environment variables

Ensure you have:

#### Groq (optional but recommended)

If you want to use Groq as the primary LLM:

- Install `groq` (already included in `requirements.txt`).
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

---

## Running the API

From the project root:

```bash
uvicorn api.main:app --reload --port 8000
```

Key endpoints:

- **Query endpoint:** `POST /query`
- **Ingest file:** `POST /ingest/file`
- **Ingest URL:** `POST /ingest/url`
- **Ingest folder:** `POST /ingest/folder`

Interactive docs:

- Swagger UI: `http://127.0.0.1:8000/docs`

---

## CLI Usage

### Chatbot (core agent)

```bash
python -m cli.main
```

Example:

```text
HR RAG Chatbot (type 'exit' to quit)

You: What is the annual leave policy?
Assistant: ...
```

### Chatbot (LangGraph agent)

```bash
python -m cli.langgraph_agent_main
```

### Ingestion (CLI)

```bash
# Ingest a single file into hr_policies dataset
python -m cli.ingest --path path/to/hr_policies.pdf --dataset hr_policies

# Ingest entire folder (recursively)
python -m cli.ingest --path data/hr_policies --dataset hr_policies

# Another dataset (e.g., HR data)
python -m cli.ingest --path data/hr_data --dataset hr_data

# Ingest from a URL
python -m cli.ingest --path https://example.com/hr_policy.pdf --dataset hr_policies
```

---

## Notes

- PII detection/redaction is **not active** in this version. If you need PII protection, you can re-enable usage of `pii_detector.py` and `pii_redactor.py` in the ingestion pipeline.
- The chatbot answers **only** from the ingested HR knowledge (CSV/XLSX/JSON/policy docs) and is instructed to say it does not know if the answer is not in the context.
- Answers are returned as **plain natural language** with no citations or internal document identifiers.

You can further customize retrieval, prompts, and metadata to better match your HR data model (e.g., policy type, region, department, effective dates).

```

```
