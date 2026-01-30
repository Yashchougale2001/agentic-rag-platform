# cli/langgraph_agent_main.py
import logging

from src.utils.config_loader import ensure_directories
from src.agent.graph_agent import build_it_graph_agent

logging.basicConfig(level=logging.INFO)


def main():
    ensure_directories()
    # compile() returns a runnable graph; we don't need the CompiledGraph type
    graph = build_it_graph_agent().compile()

    print("IT RAG LangGraph Agent (type 'exit' to quit)")
    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if question.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break

        # Call the compiled graph
        result = graph.invoke({"question": question})
        answer = result.get("answer", "")
        print("\nAssistant:", answer)


if __name__ == "__main__":
    main()