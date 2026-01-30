import argparse
import logging
import os
from typing import List

from src.utils.config_loader import ensure_directories
from src.ingestion.ingest_pipeline import IngestionPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ingest_path(pipeline: IngestionPipeline, path: str, dataset: str):
    if os.path.isdir(path):
        # Walk folder recursively
        for root, dirs, files in os.walk(path):
            for fname in files:
                fpath = os.path.join(root, fname)
                logger.info("Ingesting file: %s", fpath)
                res = pipeline.ingest(fpath, dataset_name=dataset)
                logger.info("  -> %s", res)
    else:
        logger.info("Ingesting file: %s", path)
        res = pipeline.ingest(path, dataset_name=dataset)
        logger.info("  -> %s", res)


def main():
    parser = argparse.ArgumentParser(description="Ingest IT assets data.")
    parser.add_argument(
        "--path",
        required=True,
        help="Local file path, folder path, or URL",
    )
    parser.add_argument("--dataset", default="it_assets", help="Dataset name")
    args = parser.parse_args()

    ensure_directories()
    pipeline = IngestionPipeline()
    ingest_path(pipeline, args.path, args.dataset)


if __name__ == "__main__":
    main()