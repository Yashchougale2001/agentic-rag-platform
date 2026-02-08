from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from pathlib import Path
import shutil
import os

from src.utils.config_loader import load_paths
from src.ingestion.ingest_pipeline import IngestionPipeline

router = APIRouter(prefix="/ingest", tags=["ingest"])

pipeline = IngestionPipeline()


class IngestResponse(BaseModel):
    status: str
    count: int


@router.post("/file", response_model=IngestResponse)
async def ingest_file(
    file: UploadFile = File(...),
    dataset: str = Form("default"),
):
    try:
        paths = load_paths()
        tmp_dir = Path(paths.get("tmp_dir", "data/tmp"))
        tmp_dir.mkdir(parents=True, exist_ok=True)
        dest = tmp_dir / file.filename
        with dest.open("wb") as f:
            shutil.copyfileobj(file.file, f)

        res = pipeline.ingest(str(dest), dataset_name=dataset)
        return IngestResponse(status=res.get("status", "ok"), count=res.get("count", 0))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/url", response_model=IngestResponse)
async def ingest_url(url: str, dataset: str = "default"):
    try:
        res = pipeline.ingest(url, dataset_name=dataset)
        return IngestResponse(status=res.get("status", "ok"), count=res.get("count", 0))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/folder", response_model=IngestResponse)
async def ingest_folder(path: str, dataset: str = "default"):
    """
    Ingest all files in a local folder (recursively).

    NOTE: 'path' is a server-side local path (e.g. 'data/hr_policies'),
    not a path on the client machine.
    """
    try:
        if not os.path.isdir(path):
            raise HTTPException(status_code=400, detail=f"'{path}' is not a directory or does not exist")

        total_chunks = 0
        # Walk folder recursively and ingest each file
        for root, dirs, files in os.walk(path):
            for fname in files:
                fpath = os.path.join(root, fname)
                res = pipeline.ingest(fpath, dataset_name=dataset)
                total_chunks += res.get("count", 0)

        return IngestResponse(status="ok", count=total_chunks)
    except HTTPException:
        # re-raise FastAPI HTTP errors as-is
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))