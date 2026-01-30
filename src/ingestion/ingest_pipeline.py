import logging
from typing import List, Dict, Optional
from pathlib import Path

from src.utils.config_loader import load_settings, load_paths
from src.utils.file_utils import (
    get_extension,
    is_remote_path,
    download_file,
    detect_mime_type,
)
from src.ingestion.csv_loader import load_csv
from src.ingestion.yaml_loader import load_yaml_file
from src.ingestion.text_loader import load_text_file
from src.ingestion.md_loader import load_md_file
from src.processing.pii_detector import PIIDetector
from src.processing.pii_redactor import redact_pii
from src.processing.chunker import chunk_text
from src.embeddings.embedder import EmbeddingService
from src.db.vector_store import VectorStore

logger = logging.getLogger(__name__)


class IngestionPipeline:
    def __init__(self):
        self.settings = load_settings()
        self.paths = load_paths()
        self.pii_detector = PIIDetector()
        self.embedder = EmbeddingService()
        self.vector_store = VectorStore()
        self.enable_pii_redaction = self.settings.get("security", {}).get(
            "enable_pii_redaction", True
        )

    def _load_docs_from_path(self, path: str) -> List[Dict]:
        ext = get_extension(path)
        mime = detect_mime_type(path)

        if ext == ".csv":
            return load_csv(path)
        if ext in [".yml", ".yaml"]:
            return load_yaml_file(path)
        if ext in [".txt"]:
            return load_text_file(path)
        if ext in [".md", ".markdown"]:
            return load_md_file(path)
        if ext in [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".json"]:
            # Use LangChain/unstructured loaders to handle those
            from langchain_community.document_loaders import (
                PyPDFLoader,
                UnstructuredWordDocumentLoader,
                UnstructuredExcelLoader,
                JSONLoader,
            )

            docs = []
            if ext == ".pdf":
                loader = PyPDFLoader(path)
            elif ext in [".docx", ".doc"]:
                loader = UnstructuredWordDocumentLoader(path)
            elif ext in [".xlsx", ".xls"]:
                loader = UnstructuredExcelLoader(path, mode="elements")
            elif ext == ".json":
                loader = JSONLoader(path, jq_schema=".", text_content=True)
            else:
                loader = None

            if loader:
                lc_docs = loader.load()
                for i, d in enumerate(lc_docs):
                    docs.append(
                        {
                            "id": f"{Path(path).name}-{i}",
                            "text": d.page_content,
                            "metadata": {
                                "source": str(path),
                                "file_type": ext.lstrip("."),
                                **(d.metadata or {}),
                            },
                        }
                    )
            return docs

        # fallback as plain text
        return load_text_file(path)

    def ingest(
        self,
        path_or_url: str,
        dataset_name: str = "default",
        extra_metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Full pipeline: download (if URL) -> load -> PII detection/redaction -> chunk -> embed -> index
        """
        tmp_path = None
        paths_cfg = load_paths()
        tmp_dir = paths_cfg.get("tmp_dir", "data/tmp")
        Path(tmp_dir).mkdir(parents=True, exist_ok=True)

        try:
            if is_remote_path(path_or_url):
                tmp_path = download_file(path_or_url, tmp_dir)
                source_path = tmp_path
            else:
                source_path = path_or_url

            docs = self._load_docs_from_path(source_path)

            processed_docs = []
            for d in docs:
                text = d["text"]
                metadata = d.get("metadata", {})
                if extra_metadata:
                    metadata.update(extra_metadata)
                metadata["dataset"] = dataset_name

                if self.enable_pii_redaction:
                    spans = self.pii_detector.detect(text)
                    text = redact_pii(text, spans)

                chunks = chunk_text(text)
                for idx, ch in enumerate(chunks):
                    processed_docs.append(
                        {
                            "id": f"{d['id']}-chunk-{idx}",
                            "text": ch,
                            "metadata": metadata,
                        }
                    )

            if not processed_docs:
                logger.warning("No documents to ingest from %s", path_or_url)
                return {"status": "empty", "count": 0}

            texts = [d["text"] for d in processed_docs]
            metadatas = [d["metadata"] for d in processed_docs]
            ids = [d["id"] for d in processed_docs]

            embeddings = self.embedder.embed_texts(texts)
            self.vector_store.add_documents(
                ids=ids, texts=texts, metadatas=metadatas, embeddings=embeddings
            )

            logger.info(
                "Ingested %d chunks from %s into dataset %s",
                len(processed_docs),
                path_or_url,
                dataset_name,
            )
            return {"status": "ok", "count": len(processed_docs)}
        finally:
            if tmp_path:
                try:
                    Path(tmp_path).unlink()
                except Exception:
                    pass