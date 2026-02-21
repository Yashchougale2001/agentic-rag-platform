# import logging
# from typing import List, Dict, Optional
# from pathlib import Path

# from src.utils.config_loader import load_settings, load_paths
# from src.utils.file_utils import (
#     get_extension,
#     is_remote_path,
#     download_file,
# )
# from src.ingestion.csv_loader import load_csv
# from src.ingestion.yaml_loader import load_yaml_file
# from src.ingestion.text_loader import load_text_file
# from src.ingestion.md_loader import load_md_file
# from src.ingestion.xlsx_loader import load_xlsx
# from src.ingestion.json_loader import load_json
# from src.processing.chunker import chunk_text
# from src.embeddings.embedder import EmbeddingService
# from src.db.vector_store import VectorStore

# logger = logging.getLogger(__name__)


# class IngestionPipeline:
#     def __init__(self):
#         self.settings = load_settings()
#         self.paths = load_paths()
#         self.embedder = EmbeddingService()
#         self.vector_store = VectorStore()

#     def _load_docs_from_path(self, path: str) -> List[Dict]:
#         ext = get_extension(path)

#         # 1) Simple text-like formats
#         if ext == ".csv":
#             return load_csv(path)
#         if ext in [".yml", ".yaml"]:
#             return load_yaml_file(path)
#         if ext == ".txt":
#             return load_text_file(path)
#         if ext in [".md", ".markdown"]:
#             return load_md_file(path)

#         # 2) Structured tabular formats (custom loaders)
#         if ext in [".xlsx", ".xls"]:
#             return load_xlsx(path)
#         if ext == ".json":
#             return load_json(path)

#         # 3) Rich document formats via LangChain loaders (PDF, Word)
#         if ext in [".pdf", ".docx", ".doc"]:
#             from langchain_community.document_loaders import (
#                 PyPDFLoader,
#                 UnstructuredWordDocumentLoader,
#             )

#             docs: List[Dict] = []
#             if ext == ".pdf":
#                 loader = PyPDFLoader(path)
#             else:  # .docx or .doc
#                 loader = UnstructuredWordDocumentLoader(path)

#             lc_docs = loader.load()
#             for i, d in enumerate(lc_docs):
#                 docs.append(
#                     {
#                         "id": f"{Path(path).name}-{i}",
#                         "text": d.page_content,
#                         "metadata": {
#                             "source": str(path),
#                             "file_type": ext.lstrip("."),
#                             **(d.metadata or {}),
#                         },
#                     }
#                 )
#             return docs

#         # 4) Fallback: treat as plain text
#         return load_text_file(path)

#     def ingest(
#         self,
#         path_or_url: str,
#         dataset_name: str = "default",
#         extra_metadata: Optional[Dict] = None,
#     ) -> Dict:
#         """
#         Full pipeline: download (if URL) -> load -> chunk -> embed -> index
#         """
#         tmp_path = None
#         paths_cfg = load_paths()
#         tmp_dir = paths_cfg.get("tmp_dir", "data/tmp")
#         Path(tmp_dir).mkdir(parents=True, exist_ok=True)

#         try:
#             if is_remote_path(path_or_url):
#                 tmp_path = download_file(path_or_url, tmp_dir)
#                 source_path = tmp_path
#             else:
#                 source_path = path_or_url

#             docs = self._load_docs_from_path(source_path)

#             processed_docs: List[Dict] = []
#             for d in docs:
#                 text = d["text"]
#                 metadata = d.get("metadata", {}) or {}
#                 if extra_metadata:
#                     metadata.update(extra_metadata)
#                 metadata["dataset"] = dataset_name

#                 chunks = chunk_text(text)
#                 for idx, ch in enumerate(chunks):
#                     processed_docs.append(
#                         {
#                             "id": f"{d['id']}-chunk-{idx}",
#                             "text": ch,
#                             "metadata": metadata,
#                         }
#                     )

#             if not processed_docs:
#                 logger.warning("No documents to ingest from %s", path_or_url)
#                 return {"status": "empty", "count": 0}

#             texts = [d["text"] for d in processed_docs]
#             metadatas = [d["metadata"] for d in processed_docs]
#             ids = [d["id"] for d in processed_docs]

#             embeddings = self.embedder.embed_texts(texts)
#             self.vector_store.add_documents(
#                 ids=ids, texts=texts, metadatas=metadatas, embeddings=embeddings
#             )

#             logger.info(
#                 "Ingested %d chunks from %s into dataset %s",
#                 len(processed_docs),
#                 path_or_url,
#                 dataset_name,
#             )
#             return {"status": "ok", "count": len(processed_docs)}
#         finally:
#             if tmp_path:
#                 try:
#                     Path(tmp_path).unlink()
#                 except Exception:
#                     pass
import logging
from typing import List, Dict, Optional
from pathlib import Path

from src.utils.config_loader import load_settings, load_paths
from src.utils.file_utils import (
    get_extension,
    is_remote_path,
    download_file,
)
from src.ingestion.csv_loader import load_csv
from src.ingestion.yaml_loader import load_yaml_file
from src.ingestion.text_loader import load_text_file
from src.ingestion.md_loader import load_md_file
from src.ingestion.xlsx_loader import load_xlsx
from src.ingestion.json_loader import load_json
from src.processing.chunker import chunk_text
from src.embeddings.embedder import EmbeddingService
from src.db.vector_store import VectorStore

logger = logging.getLogger(__name__)


class IngestionPipeline:
    def __init__(self):
        self.settings = load_settings()
        self.paths = load_paths()
        self.embedder = EmbeddingService()
        self.vector_store = VectorStore()

    # ---------- NEW: RBAC metadata inference ---------- #

    def _infer_rbac_metadata(
        self,
        source_path: str,
        dataset_name: str,
        base_metadata: Dict,
    ) -> Dict[str, Optional[str]]:
        """
        Infer RBAC-related metadata based on dataset and file path.

        Returns dict with:
          - visibility: "public" | "hr" | "admin" | "private"
          - owner_user_id: str (optional, for private docs)
        """
        # If already explicitly set, respect it
        visibility = base_metadata.get("visibility")
        owner_user_id = base_metadata.get("owner_user_id")

        if visibility:
            return {"visibility": visibility, "owner_user_id": owner_user_id}

        path = str(source_path).replace("\\", "/").lower()
        ds = dataset_name.lower()

        # ----- hr_data -----
        if ds == "hr_data":
            if "employee_data.csv" in path or "synthetic_health_benefits_500.csv" in path:
                visibility = "private"
                # Try to infer owner from existing metadata keys (if present)
                owner_user_id = (
                    base_metadata.get("employee_id")
                    or base_metadata.get("EmployeeID")
                    or base_metadata.get("email")
                    or base_metadata.get("Email")
                    or owner_user_id
                )
            elif (
                "employee_engagement_survey_data.csv" in path
                or "recruitment_data.csv" in path
                or "training_and_development_data.csv" in path
            ):
                visibility = "hr"
            elif "hr_policy_dat.xlsx" in path or "policies_index.json" in path:
                visibility = "public"
            else:
                visibility = "public"

        # ----- hr_local -----
        elif ds == "hr_local":
            visibility = "public"

        # ----- hr_policies -----
        elif ds == "hr_policies":
            visibility = "public"  # change to "hr" if you have internal-only policies

        # ----- it_assets -----
        elif ds == "it_assets":
            if "/it_assets/network/" in path:
                visibility = "admin"
            elif "/it_assets/users/" in path:
                visibility = "private"
                owner_user_id = (
                    base_metadata.get("user_id")
                    or base_metadata.get("employee_id")
                    or base_metadata.get("email")
                    or owner_user_id
                )
            elif "/it_assets/hardware/" in path:
                visibility = "hr"
            else:
                visibility = "public"

        # Fallback
        if not visibility:
            visibility = "public"

        return {"visibility": visibility, "owner_user_id": owner_user_id}

    # ---------- existing methods ---------- #

    def _load_docs_from_path(self, path: str) -> List[Dict]:
        ext = get_extension(path)

        # 1) Simple text-like formats
        if ext == ".csv":
            return load_csv(path)
        if ext in [".yml", ".yaml"]:
            return load_yaml_file(path)
        if ext == ".txt":
            return load_text_file(path)
        if ext in [".md", ".markdown"]:
            return load_md_file(path)

        # 2) Structured tabular formats (custom loaders)
        if ext in [".xlsx", ".xls"]:
            return load_xlsx(path)
        if ext == ".json":
            return load_json(path)

        # 3) Rich document formats via LangChain loaders (PDF, Word)
        if ext in [".pdf", ".docx", ".doc"]:
            from langchain_community.document_loaders import (
                PyPDFLoader,
                UnstructuredWordDocumentLoader,
            )

            docs: List[Dict] = []
            if ext == ".pdf":
                loader = PyPDFLoader(path)
            else:  # .docx or .doc
                loader = UnstructuredWordDocumentLoader(path)

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

        # 4) Fallback: treat as plain text
        return load_text_file(path)

    def ingest(
        self,
        path_or_url: str,
        dataset_name: str = "default",
        extra_metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Full pipeline: download (if URL) -> load -> chunk -> embed -> index
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

            processed_docs: List[Dict] = []
            for d in docs:
                text = d["text"]
                metadata = d.get("metadata", {}) or {}

                if extra_metadata:
                    metadata.update(extra_metadata)

                metadata["dataset"] = dataset_name

                # ---------- NEW: inject RBAC metadata ----------
                rbac_meta = self._infer_rbac_metadata(
                    source_path=source_path,
                    dataset_name=dataset_name,
                    base_metadata=metadata,
                )
                metadata.update(rbac_meta)
                # ---------------------------------------------- #

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