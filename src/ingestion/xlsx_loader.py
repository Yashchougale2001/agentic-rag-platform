# src/ingestion/xlsx_loader.py
from typing import List, Dict, Optional
from pathlib import Path
import pandas as pd


def load_xlsx(
    path: str,
    sheet_name: Optional[str] = None,
) -> List[Dict]:
    """
    Load an .xlsx/.xls file and convert each row into a text document
    similar to csv_loader.

    - Each row -> one doc
    - Text: "col1: val1 col2: val2 ..."
    - metadata: source, row_index, sheet_name, file_type
    """
    # Read all sheets or specific one
    if sheet_name is None:
        xls = pd.read_excel(path, sheet_name=None)  # dict of sheet_name -> DataFrame
    else:
        xls = {sheet_name: pd.read_excel(path, sheet_name=sheet_name)}

    docs: List[Dict] = []
    for sname, df in xls.items():
        for idx, row in df.iterrows():
            parts = []
            for col in df.columns:
                val = row[col]
                if pd.isna(val):
                    continue
                parts.append(f"{col}: {val}")
            text = " ".join(parts)

            docs.append(
                {
                    "id": f"{Path(path).name}-{sname}-{idx}",
                    "text": text,
                    "metadata": {
                        "source": str(path),
                        "row_index": int(idx),
                        "sheet_name": sname,
                        "file_type": "xlsx",
                    },
                }
            )

    return docs