from typing import Dict, List
from src.retrieval.retriever import Retriever


class RAGTool:
    """
    Tool that performs retrieval given a user query.
    """

    def __init__(self):
        self.retriever = Retriever()

    def run(self, query: str) -> List[Dict]:
        return self.retriever.retrieve(query)