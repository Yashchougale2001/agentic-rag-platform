# """
# CLI interface for the agentic chatbot (aligned with LangGraph agent + API).
# """

# from __future__ import annotations

# import argparse
# from typing import List, Literal, Dict, Any

# from rich.console import Console
# from rich.markdown import Markdown
# from rich.panel import Panel
# from rich.table import Table

# from src.agent.graph_agent import build_basic_hr_agent

# console = Console()

# RoleLiteral = Literal["admin", "hr", "employee"]


# # -------------------- Agent wrapper -------------------- #

# def build_agent():
#     """Build and compile the LangGraph agent once."""
#     graph = build_basic_hr_agent().compile()
#     return graph


# def invoke_agent(
#     graph: Any,
#     question: str,
#     user_id: str,
#     role: RoleLiteral,
# ) -> Dict[str, Any]:
#     """
#     Invoke the compiled graph and normalize the result into the same
#     shape as the API uses: answer, steps, context_sources.
#     """
#     state = graph.invoke(
#         {
#             "question": question,
#             "user_id": user_id,
#             "role": role,
#         }
#     ) or {}

#     answer: str = state.get("answer") or ""
#     steps: List[str] = state.get("steps") or []
#     context: List[Dict[str, Any]] = state.get("context") or []

#     context_sources = sorted(
#         {
#             d.get("metadata", {}).get("source", "unknown")
#             for d in context
#         }
#     )

#     return {
#         "answer": answer,
#         "steps": steps,
#         "context_sources": context_sources,
#     }


# # -------------------- UI helpers -------------------- #

# def display_response(result: Dict[str, Any]) -> None:
#     """Display the agent response with formatting."""
#     console.print("\n")

#     # Main answer
#     console.print(
#         Panel(
#             Markdown(result["answer"] or "_No answer generated._"),
#             title="[bold green]Agent Response[/bold green]",
#             border_style="green",
#         )
#     )

#     # Context sources (KB + local files, memory, profile, etc.)
#     sources = result.get("context_sources") or []
#     if sources:
#         table = Table(title="Context Sources", show_header=True)
#         table.add_column("Source", style="cyan")
#         for src in sources:
#             table.add_row(str(src))
#         console.print(table)

#     # Steps trace (planner + tools)
#     steps = result.get("steps") or []
#     if steps:
#         console.print(
#             f"\n[dim]Steps: {' -> '.join(steps)}[/dim]\n"
#         )
#     else:
#         console.print("\n[dim]Steps: [none][/dim]\n")


# def choose_role(default: RoleLiteral = "employee") -> RoleLiteral:
#     """Ask user for a role if not given via CLI."""
#     valid = {"admin", "hr", "employee"}

#     while True:
#         role = console.input(
#             f"[bold]Enter role[/bold] [admin/hr/employee] (default: {default}): "
#         ).strip().lower()

#         if not role:
#             return default  # use default on empty

#         if role in valid:
#             return role  # type: ignore[return-value]

#         console.print("[red]Invalid role. Please enter 'admin', 'hr', or 'employee'.[/red]")


# # -------------------- Modes -------------------- #

# def interactive_mode(graph: Any, user_id: str, role: RoleLiteral) -> None:
#     """Run the agent in interactive mode with fixed user_id and role."""
#     console.print(
#         Panel(
#             "[bold]Welcome to the Agentic Assistant[/bold]\n\n"
#             f"User ID: [cyan]{user_id}[/cyan]\n"
#             f"Role: [magenta]{role}[/magenta]\n\n"
#             "I can help you with:\n"
#             "• Searching the knowledge base\n"
#             "• Looking up policies\n"
#             "• Finding employee / IT asset information\n\n"
#             "Type 'quit' or 'exit' to end the session.",
#             title="🤖 Agent Ready",
#             border_style="blue",
#         )
#     )

#     while True:
#         try:
#             query = console.input("\n[bold cyan]You:[/bold cyan] ").strip()

#             if not query:
#                 continue

#             if query.lower() in {"quit", "exit", "q"}:
#                 console.print("[yellow]Goodbye![/yellow]")
#                 break

#             with console.status("[bold green]Thinking...[/bold green]"):
#                 result = invoke_agent(graph, query, user_id=user_id, role=role)

#             display_response(result)

#         except KeyboardInterrupt:
#             console.print("\n[yellow]Session interrupted.[/yellow]")
#             break
#         except Exception as e:
#             console.print(f"[red]Error: {str(e)}[/red]")


# def single_query_mode(
#     graph: Any,
#     query: str,
#     user_id: str,
#     role: RoleLiteral,
# ) -> None:
#     """Run a single query and exit."""
#     with console.status("[bold green]Processing...[/bold green]"):
#         result = invoke_agent(graph, query, user_id=user_id, role=role)

#     display_response(result)


# # -------------------- CLI entrypoint -------------------- #

# def main() -> None:
#     parser = argparse.ArgumentParser(description="Agentic Chatbot CLI (LangGraph)")
#     parser.add_argument(
#         "-q",
#         "--query",
#         type=str,
#         help="Single query to process (non-interactive mode)",
#     )
#     parser.add_argument(
#         "--user-id",
#         "-u",
#         type=str,
#         default=None,
#         help="User ID for memory and RBAC (default: 'cli_user')",
#     )
#     parser.add_argument(
#         "--role",
#         "-r",
#         type=str,
#         choices=["admin", "hr", "employee"],
#         default=None,
#         help="User role for RBAC (default: ask; fallback to 'employee')",
#     )

#     args = parser.parse_args()

#     # Determine identity
#     user_id = args.user_id or "cli_user"
#     role: RoleLiteral
#     if args.role:
#         role = args.role  # type: ignore[assignment]
#     else:
#         # Ask interactively if not provided
#         role = choose_role(default="employee")

#     console.print("[dim]Initializing agent...[/dim]")
#     graph = build_agent()

#     if args.query:
#         single_query_mode(graph, args.query, user_id=user_id, role=role)
#     else:
#         interactive_mode(graph, user_id=user_id, role=role)


# if __name__ == "__main__":
#     main()
"""
CLI interface for the agentic chatbot (aligned with LangGraph agent + API).

Features:
- Uses LangGraph agent from build_basic_hr_agent()
- Supports user_id + role (admin/hr/employee)
- Allows switching role and user_id mid-conversation
- Requires admin login (username + password) before using admin role
"""

from __future__ import annotations

import argparse
import os
import getpass
from typing import List, Literal, Dict, Any, Tuple, Optional

from dotenv import load_dotenv  # NEW
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from src.agent.graph_agent import build_basic_hr_agent

# Load .env so ADMIN_USER, ADMIN_PASSWORD, GROQ_API_KEY are available
load_dotenv()

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


# -------------------- Admin auth helpers -------------------- #

def get_admin_config() -> Tuple[str, Optional[str]]:
    """
    Return configured admin username and password.

    ADMIN_USER defaults to 'admin'.
    ADMIN_PASSWORD must be set for admin login to work.
    """
    admin_user = os.getenv("ADMIN_USER", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD")  # no default for security
    return admin_user, admin_password


def admin_login() -> Tuple[Optional[str], bool]:
    """
    Prompt for admin username + password and validate against env config.

    Returns:
      (admin_username_if_ok, authenticated_bool)
    """
    configured_user, configured_pass = get_admin_config()

    if configured_pass is None:
        console.print(
            "[red]ADMIN_PASSWORD environment variable is not set. "
            "Admin login is disabled.[/red]"
        )
        return None, False

    console.print("\n[bold yellow]Admin login required[/bold yellow] 🔐")
    username = console.input("[bold]Admin username:[/bold] ").strip()
    password = getpass.getpass("Admin password: ")

    if username == configured_user and password == configured_pass:
        console.print("[green]✅ Admin authenticated.[/green]")
        return username, True

    console.print("[red]❌ Invalid admin credentials.[/red]")
    return None, False


# -------------------- UI helpers -------------------- #

def display_response(result: Dict[str, Any]) -> None:
    """Display the agent response with formatting."""
    console.print("\n")

    # Main answer
    console.print(
        Panel(
            Markdown(result["answer"] or "_No answer generated._"),
            title="🤖 [bold green]Agent Response[/bold green]",
            border_style="green",
        )
    )

    # Context sources (KB + local files, profile, etc.)
    sources = result.get("context_sources") or []
    if sources:
        table = Table(title="📚 Context Sources", show_header=True)
        table.add_column("Source", style="cyan")
        for src in sources:
            table.add_row(str(src))
        console.print(table)

    # Steps trace (planner + tools)
    steps = result.get("steps") or []
    if steps:
        console.print(f"\n[dim]Steps: {' -> '.join(steps)}[/dim]\n")
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


def show_help_commands() -> None:
    """Show available slash commands."""
    console.print(
        Panel(
            "[bold]Commands[/bold]\n\n"
            "• /role <admin|hr|employee>  – switch role\n"
            "• /user <user_id>           – switch user ID\n"
            "• /whoami                   – show current user and role\n"
            "• /help                     – show this help\n"
            "• quit / exit / q           – exit the session",
            title="ℹ️ Commands",
            border_style="cyan",
        )
    )


# -------------------- Interactive logic -------------------- #

def handle_command(
    cmd: str,
    current_user_id: str,
    current_role: RoleLiteral,
    admin_authenticated: bool,
    admin_user_id: Optional[str],
) -> Tuple[bool, str, RoleLiteral, bool, Optional[str]]:
    """
    Handle slash-commands like /role, /user, /whoami, /help.

    Returns:
      (handled, new_user_id, new_role, new_admin_authenticated, new_admin_user_id)
    """
    parts = cmd.strip().split()
    if not parts:
        return False, current_user_id, current_role, admin_authenticated, admin_user_id

    name = parts[0].lower()

    # /help
    if name == "/help":
        show_help_commands()
        return True, current_user_id, current_role, admin_authenticated, admin_user_id

    # /whoami
    if name == "/whoami":
        console.print(
            f"[bold]Current user:[/bold] [cyan]{current_user_id}[/cyan], "
            f"[bold]role:[/bold] [magenta]{current_role}[/magenta]"
        )
        return True, current_user_id, current_role, admin_authenticated, admin_user_id

    # /user <id>
    if name == "/user" and len(parts) >= 2:
        new_id = " ".join(parts[1:]).strip()
        if not new_id:
            console.print("[red]Usage: /user <user_id>[/red]")
            return True, current_user_id, current_role, admin_authenticated, admin_user_id
        console.print(f"[green]✔ Switched user_id to[/green] [cyan]{new_id}[/cyan]")
        return True, new_id, current_role, admin_authenticated, admin_user_id

    # /role <admin|hr|employee>
    if name == "/role" and len(parts) >= 2:
        new_role_raw = parts[1].lower()
        if new_role_raw not in {"admin", "hr", "employee"}:
            console.print("[red]Usage: /role <admin|hr|employee>[/red]")
            return True, current_user_id, current_role, admin_authenticated, admin_user_id

        new_role: RoleLiteral = new_role_raw  # type: ignore[assignment]

        # If switching to admin, require login if not already authenticated
        if new_role == "admin":
            if not admin_authenticated:
                admin_username, ok = admin_login()
                if not ok:
                    console.print("[yellow]Staying in previous role.[/yellow]")
                    return True, current_user_id, current_role, admin_authenticated, admin_user_id
                # Admin authenticated successfully
                admin_authenticated = True
                admin_user_id = admin_username or "admin"
                # For RBAC consistency, set user_id to admin username
                current_user_id = admin_user_id
                current_role = new_role
                console.print(
                    f"[green]✔ Switched role to[/green] [magenta]{current_role}[/magenta] "
                    f"as [cyan]{current_user_id}[/cyan]"
                )
                return True, current_user_id, current_role, admin_authenticated, admin_user_id
            else:
                # Already authenticated as admin
                current_role = new_role
                if admin_user_id:
                    current_user_id = admin_user_id
                console.print(
                    f"[green]✔ Switched role to[/green] [magenta]{current_role}[/magenta] "
                    f"as [cyan]{current_user_id}[/cyan]"
                )
                return True, current_user_id, current_role, admin_authenticated, admin_user_id

        # Switching away from admin
        current_role = new_role
        console.print(
            f"[green]✔ Switched role to[/green] [magenta]{current_role}[/magenta]"
        )
        return True, current_user_id, current_role, admin_authenticated, admin_user_id

    # Unknown command starting with '/'
    if name.startswith("/"):
        console.print("[red]Unknown command. Type /help for available commands.[/red]")
        return True, current_user_id, current_role, admin_authenticated, admin_user_id

    return False, current_user_id, current_role, admin_authenticated, admin_user_id


def interactive_mode(
    graph: Any,
    user_id: str,
    role: RoleLiteral,
    admin_authenticated: bool,
    admin_user_id: Optional[str],
) -> None:
    """Run the agent in interactive mode with current user_id and role."""
    console.print(
        Panel(
            "🤖 [bold]Welcome to the Agentic Assistant[/bold]\n\n"
            f"User ID: [cyan]{user_id}[/cyan]\n"
            f"Role: [magenta]{role}[/magenta]\n\n"
            "I can help you with:\n"
            "• Searching the knowledge base\n"
            "• Looking up policies\n"
            "• Finding employee / IT asset information\n\n"
            "Type /help to see commands.\n"
            "Type 'quit' or 'exit' to end the session.",
            title="Agent Ready",
            border_style="blue",
        )
    )

    current_user_id = user_id
    current_role = role

    while True:
        try:
            query = console.input("\n[bold cyan]You:[/bold cyan] ").strip()

            if not query:
                continue

            if query.lower() in {"quit", "exit", "q"}:
                console.print("👋 [yellow]Goodbye![/yellow]")
                break

            # Slash-commands
            if query.startswith("/"):
                handled, current_user_id, current_role, admin_authenticated, admin_user_id = handle_command(
                    query,
                    current_user_id,
                    current_role,
                    admin_authenticated,
                    admin_user_id,
                )
                if handled:
                    continue

            with console.status("🤖 [bold green]Thinking...[/bold green]"):
                result = invoke_agent(
                    graph,
                    query,
                    user_id=current_user_id,
                    role=current_role,
                )

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
    admin_authenticated: bool,
    admin_user_id: Optional[str],
) -> None:
    """Run a single query and exit."""
    # If single query is admin and not authenticated yet, enforce login
    if role == "admin" and not admin_authenticated:
        admin_username, ok = admin_login()
        if not ok:
            console.print("[yellow]Falling back to employee role for this query.[/yellow]")
            role = "employee"
        else:
            admin_authenticated = True
            admin_user_id = admin_username or "admin"
            user_id = admin_user_id

    with console.status("🤖 [bold green]Processing...[/bold green]"):
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
        help="User ID for memory and RBAC (default: 'cli_user' or admin username)",
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

    # Determine initial identity
    initial_role: RoleLiteral
    if args.role:
        initial_role = args.role  # type: ignore[assignment]
    else:
        initial_role = choose_role(default="employee")

    admin_authenticated = False
    admin_user_id: Optional[str] = None

    # If starting as admin, enforce login immediately
    if initial_role == "admin":
        admin_username, ok = admin_login()
        if not ok:
            console.print("[yellow]Falling back to employee role.[/yellow]")
            initial_role = "employee"
        else:
            admin_authenticated = True
            admin_user_id = admin_username or "admin"

    # Initial user_id
    if initial_role == "admin" and admin_user_id is not None:
        initial_user_id = admin_user_id
    else:
        initial_user_id = args.user_id or "cli_user"

    console.print("[dim]Initializing agent...[/dim]")
    graph = build_agent()

    if args.query:
        single_query_mode(
            graph,
            args.query,
            user_id=initial_user_id,
            role=initial_role,
            admin_authenticated=admin_authenticated,
            admin_user_id=admin_user_id,
        )
    else:
        interactive_mode(
            graph,
            user_id=initial_user_id,
            role=initial_role,
            admin_authenticated=admin_authenticated,
            admin_user_id=admin_user_id,
        )


if __name__ == "__main__":
    main()