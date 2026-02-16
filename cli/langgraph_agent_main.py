# from src.agent.graph_agent import build_graph_agent


# def main():
#     print("General Chatbot (LangGraph Agent)")
#     print("Type 'quit' to exit, 'debug' for step-by-step mode\n")

#     agent = build_graph_agent()
#     debug_mode = False

#     while True:
#         user_input = input("You: ").strip()

#         if not user_input:
#             continue

#         if user_input.lower() == "quit":
#             print("Goodbye!")
#             break

#         if user_input.lower() == "debug":
#             debug_mode = not debug_mode
#             print(f"Debug mode: {'ON' if debug_mode else 'OFF'}")
#             continue

#         try:
#             if debug_mode:
#                 print("\n--- Agent Execution Steps ---")
#                 for step in agent.stream(user_input):
#                     node_name = list(step.keys())[0]
#                     print(f"  → {node_name}")
#                 result = agent.invoke(user_input)
#             else:
#                 result = agent.invoke(user_input)

#             print(f"\nAssistant: {result['answer']}")

#             if debug_mode:
#                 print(f"\n[Steps: {' → '.join(result['steps'])}]")
#                 print(f"[Intent: {result.get('intent', 'N/A')}]")
#                 print(f"[Retrieval Attempts: {result.get('retrieval_attempts', 0)}]")

#             print()

#         except Exception as e:
#             print(f"Error: {e}\n")


# if __name__ == "__main__":
#     main()
# cli/langgraph_agent_main.py

from __future__ import annotations

import argparse
import logging
import sys

from src.agent.graph_agent import build_basic_hr_agent
from src.utils.logging_config import setup_logging  # adjust if your name is different


logger = logging.getLogger(__name__)


def run_cli(show_steps: bool = False) -> None:
    """
    Interactive REPL for the LangGraph HR/IT-assets agent.
    """
    setup_logging()
    logger.info("Starting LangGraph HR/IT-assets CLI agent")

    # Build and compile the graph once
    graph = build_basic_hr_agent().compile()

    print("=" * 60)
    print(" HR / IT-Assets Assistant (LangGraph)")
    print("=" * 60)
    print("Type your question and press Enter.")
    print("Type 'exit', 'quit', or 'q' to leave.")
    if show_steps:
        print("Debug: step trace is ENABLED.\n")
    else:
        print("Debug: step trace is disabled (use --show-steps to enable).\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting. Goodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit", "q", ":q"}:
            print("Goodbye!")
            break

        try:
            # Each call is a fresh state: {"question": <user query>}
            result = graph.invoke({"question": user_input})
        except Exception as e:
            logger.exception("Error while running agent: %s", e)
            print(f"\n[Error] Something went wrong: {e}")
            continue

        answer = (result or {}).get("answer") or "[No answer generated]"
        steps = (result or {}).get("steps") or []

        print("\nAssistant:\n")
        print(answer)
        print()

        if show_steps:
            print("---- Debug: Steps ----")
            if steps:
                print(" -> ".join(steps))
            else:
                print("[no steps recorded]")
            print("----------------------\n")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Interactive CLI for the LangGraph HR/IT-assets assistant."
    )
    parser.add_argument(
        "--show-steps",
        action="store_true",
        help="Print internal step trace after each answer.",
    )
    args = parser.parse_args(argv)

    run_cli(show_steps=args.show_steps)


if __name__ == "__main__":
    main(sys.argv[1:])