from typing import List, Dict
import pandas as pd
from pathlib import Path


def load_csv(path: str) -> List[Dict]:
    df = pd.read_csv(path)
    docs = []
    for idx, row in df.iterrows():
        text = " ".join([f"{col}: {row[col]}" for col in df.columns])
        docs.append(
            {
                "id": f"{Path(path).name}-{idx}",
                "text": text,
                "metadata": {
                    "source": str(path),
                    "row_index": int(idx),
                    "file_type": "csv",
                },
            }
        )
    return docs