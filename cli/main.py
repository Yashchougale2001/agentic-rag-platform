"""
CLI interface for the agentic chatbot (aligned with LangGraph agent + API).
"""

from __future__ import annotations

import argparse
from typing import List, Literal, Dict, Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from src.agent.graph_agent import build_basic_hr_agent

console = Console()

RoleLiteral = Literal["admin", "hr", "employee"]


# -------------------- Agent wrapper -------------------- #

def build_agent():
    """Build and compile the LangGraph agent once."""
    graph = build_basic_hr_agent().compile()
    return graph


def invoke_agent(
    graph: Any,
    question: str,
    user_id: str,
    role: RoleLiteral,
) -> Dict[str, Any]:
    """
    Invoke the compiled graph and normalize the result into the same
    shape as the API uses: answer, steps, context_sources.
    """
    state = graph.invoke(
        {
            "question": question,
            "user_id": user_id,
            "role": role,
        }
    ) or {}

    answer: str = state.get("answer") or ""
    steps: List[str] = state.get("steps") or []
    context: List[Dict[str, Any]] = state.get("context") or []

    context_sources = sorted(
        {
            d.get("metadata", {}).get("source", "unknown")
            for d in context
        }
    )

    return {
        "answer": answer,
        "steps": steps,
        "context_sources": context_sources,
    }


# -------------------- UI helpers -------------------- #

def display_response(result: Dict[str, Any]) -> None:
    """Display the agent response with formatting."""
    console.print("\n")

    # Main answer
    console.print(
        Panel(
            Markdown(result["answer"] or "_No answer generated._"),
            title="[bold green]Agent Response[/bold green]",
            border_style="green",
        )
    )

    # Context sources (KB + local files, memory, profile, etc.)
    sources = result.get("context_sources") or []
    if sources:
        table = Table(title="Context Sources", show_header=True)
        table.add_column("Source", style="cyan")
        for src in sources:
            table.add_row(str(src))
        console.print(table)

    # Steps trace (planner + tools)
    steps = result.get("steps") or []
    if steps:
        console.print(
            f"\n[dim]Steps: {' -> '.join(steps)}[/dim]\n"
        )
    else:
        console.print("\n[dim]Steps: [none][/dim]\n")


def choose_role(default: RoleLiteral = "employee") -> RoleLiteral:
    """Ask user for a role if not given via CLI."""
    valid = {"admin", "hr", "employee"}

    while True:
        role = console.input(
            f"[bold]Enter role[/bold] [admin/hr/employee] (default: {default}): "
        ).strip().lower()

        if not role:
            return default  # use default on empty

        if role in valid:
            return role  # type: ignore[return-value]

        console.print("[red]Invalid role. Please enter 'admin', 'hr', or 'employee'.[/red]")


# -------------------- Modes -------------------- #

def interactive_mode(graph: Any, user_id: str, role: RoleLiteral) -> None:
    """Run the agent in interactive mode with fixed user_id and role."""
    console.print(
        Panel(
            "[bold]Welcome to the Agentic Assistant[/bold]\n\n"
            f"User ID: [cyan]{user_id}[/cyan]\n"
            f"Role: [magenta]{role}[/magenta]\n\n"
            "I can help you with:\n"
            "• Searching the knowledge base\n"
            "• Looking up policies\n"
            "• Finding employee / IT asset information\n\n"
            "Type 'quit' or 'exit' to end the session.",
            title="🤖 Agent Ready",
            border_style="blue",
        )
    )

    while True:
        try:
            query = console.input("\n[bold cyan]You:[/bold cyan] ").strip()

            if not query:
                continue

            if query.lower() in {"quit", "exit", "q"}:
                console.print("[yellow]Goodbye![/yellow]")
                break

            with console.status("[bold green]Thinking...[/bold green]"):
                result = invoke_agent(graph, query, user_id=user_id, role=role)

            display_response(result)

        except KeyboardInterrupt:
            console.print("\n[yellow]Session interrupted.[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")


def single_query_mode(
    graph: Any,
    query: str,
    user_id: str,
    role: RoleLiteral,
) -> None:
    """Run a single query and exit."""
    with console.status("[bold green]Processing...[/bold green]"):
        result = invoke_agent(graph, query, user_id=user_id, role=role)

    display_response(result)


# -------------------- CLI entrypoint -------------------- #

def main() -> None:
    parser = argparse.ArgumentParser(description="Agentic Chatbot CLI (LangGraph)")
    parser.add_argument(
        "-q",
        "--query",
        type=str,
        help="Single query to process (non-interactive mode)",
    )
    parser.add_argument(
        "--user-id",
        "-u",
        type=str,
        default=None,
        help="User ID for memory and RBAC (default: 'cli_user')",
    )
    parser.add_argument(
        "--role",
        "-r",
        type=str,
        choices=["admin", "hr", "employee"],
        default=None,
        help="User role for RBAC (default: ask; fallback to 'employee')",
    )

    args = parser.parse_args()

    # Determine identity
    user_id = args.user_id or "cli_user"
    role: RoleLiteral
    if args.role:
        role = args.role  # type: ignore[assignment]
    else:
        # Ask interactively if not provided
        role = choose_role(default="employee")

    console.print("[dim]Initializing agent...[/dim]")
    graph = build_agent()

    if args.query:
        single_query_mode(graph, args.query, user_id=user_id, role=role)
    else:
        interactive_mode(graph, user_id=user_id, role=role)


if __name__ == "__main__":
    main()