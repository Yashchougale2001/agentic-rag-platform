import logging
import sys

from src.utils.config_loader import ensure_directories
from src.agent.agent_core import ITRAGAgentCore

logging.basicConfig(level=logging.INFO)


def main():
    ensure_directories()
    agent = ITRAGAgentCore()

    print("IT RAG Chatbot (type 'exit' to quit)")
    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if question.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break

        state = agent.run_rag(question)
        print("\nAssistant:", state.answer)


if __name__ == "__main__":
    main()