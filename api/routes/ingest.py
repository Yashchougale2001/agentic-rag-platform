from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from pathlib import Path
import shutil

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