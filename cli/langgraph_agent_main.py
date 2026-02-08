from src.agent.graph_agent import build_graph_agent


def main():
    print("General Chatbot (LangGraph Agent)")
    print("Type 'quit' to exit, 'debug' for step-by-step mode\n")

    agent = build_graph_agent()
    debug_mode = False

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("Goodbye!")
            break

        if user_input.lower() == "debug":
            debug_mode = not debug_mode
            print(f"Debug mode: {'ON' if debug_mode else 'OFF'}")
            continue

        try:
            if debug_mode:
                print("\n--- Agent Execution Steps ---")
                for step in agent.stream(user_input):
                    node_name = list(step.keys())[0]
                    print(f"  → {node_name}")
                result = agent.invoke(user_input)
            else:
                result = agent.invoke(user_input)

            print(f"\nAssistant: {result['answer']}")

            if debug_mode:
                print(f"\n[Steps: {' → '.join(result['steps'])}]")
                print(f"[Intent: {result.get('intent', 'N/A')}]")
                print(f"[Retrieval Attempts: {result.get('retrieval_attempts', 0)}]")

            print()

        except Exception as e:
            print(f"Error: {e}\n")


if __name__ == "__main__":
    main()