# IT Agentic RAG Chatbot

Agentic RAG chatbot for IT assets, using:

A modular, agent-driven Retrieval-Augmented Generation (RAG) platform using LangGraph for orchestration, Groq LLM with TinyLLaMA fallback, local BGE-Small embeddings, and ChromaDB.

Supports secure document ingestion (local & remote), PII detection/redaction, and is accessible via both REST API (FastAPI) and CLI.

- LangGraph agent orchestration
- Groq LLM (primary) with fallback to TinyLLaMA via Ollama
- BGE-Small embeddings (local)
- ChromaDB vector store
- PII detection & redaction
- REST API (FastAPI) + CLI

It’s designed to be:

Modular (you can swap LLMs/embedders/vector stores later)
Agentic (LangGraph-based RAG agent)
IT-assets-focused, with PII detection/redaction
Able to ingest local & remote files (CSV, TXT, MD, YAML)
Exposed through both CLI and REST API (FastAPI)

rag_agent/
│
├── config/
│ ├── **init**.py
│ ├── settings.yaml
│ ├── model.yaml
│ └── paths.yaml
│
├── data/
│
├── src/
│ ├── **init**.py
│ ├── ingestion/
│ │ ├── **init**.py
│ │ ├── csv_loader.py
│ │ ├── yaml_loader.py
│ │ ├── text_loader.py
│ │ ├── md_loader.py
│ │ └── ingest_pipeline.py
│ │
│ ├── processing/
│ │ ├── **init**.py
│ │ ├── pii_detector.py
│ │ ├── pii_redactor.py
│ │ └── chunker.py
│ │
│ ├── embeddings/
│ │ ├── **init**.py
│ │ ├── bge_model.py
│ │ └── embedder.py
│ │
│ ├── db/
│ │ ├── **init**.py
│ │ ├── chroma_client.py
│ │ └── vector_store.py
│ │
│ ├── retrieval/
│ │ ├── **init**.py
│ │ └── retriever.py
│ │
│ ├── llm/
│ │ ├── **init**.py
│ │ ├── ollama_client.py
│ │ ├── chroma_model.py
│ │ └── generator.py
│ │
│ ├── agent/
│ │ ├── **init**.py
│ │ ├── agent_core.py
│ │ ├── graph_agent.py
│ │ └── agent_tools/
│ │ ├── **init**.py
│ │ ├── rag_tool.py
│ │ └── analyze_asset.py
│ │
│ └── utils/
│ ├── **init**.py
│ ├── config_loader.py
│ └── file_utils.py
│
├── cli/
│ ├── **init**.py
│ ├── main.py
│ ├── ingest.py
│ └── langgraph_agent_main.py
│
├── api/
│ ├── **init**.py
│ ├── main.py
│ └── routes/
│ ├── **init**.py
│ ├── query.py
│ └── ingest.py
│
├── requirements.txt
├── README.md
└── .gitignore

## Setup

```bash
git clone <this-repo>
cd agentic-rag-platform
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
Ensure you have:

GROQ_API_KEY set in your environment if you want to use Groq:
Bash

export GROQ_API_KEY="your_key_here"
To set it for this shell
$env:GROQ_API_KEY = "sk_your_real_key_here"
Ollama installed and running with a tinyllama model:
Bash

ollama pull tinyllama
Running the API
Bash

Ingestion
Bash

python -m cli.ingest --path path/to/it_assets.pdf --dataset it_assets
# Ingest entire folder (recursively)
python -m cli.ingest --path data/it_assets --dataset it_assets

uvicorn api.main:app --reload --port 8000
Query endpoint: POST /query
Ingest file: POST /ingest/file
Ingest URL: POST /ingest/url
CLI
Chatbot
Bash

python -m cli.main

LangGraph Agent CLI
Bash

python -m cli.langgraph_agent_main
Notes
All ingested content is passed through a basic PII detector and redacted before embedding and storage.
The chatbot answers only from the ingested HR policy knowledge and will refuse to hallucinate answers when context is missing.
```
