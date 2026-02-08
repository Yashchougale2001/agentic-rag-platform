"""
CLI interface for the agentic chatbot.
"""

import argparse
import asyncio
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from src.agent.graph_agent import create_agent, GraphAgent


console = Console()


def display_response(result: dict):
    """Display the agent response with formatting."""
    console.print("\n")
    
    # Display main response
    console.print(Panel(
        Markdown(result["response"]),
        title="[bold green]Agent Response[/bold green]",
        border_style="green"
    ))
    
    # Display tool calls if any
    if result["tool_calls"]:
        table = Table(title="Tools Used", show_header=True)
        table.add_column("Tool", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Summary", style="white")
        
        for tc in result["tool_calls"]:
            status = "✓ Success" if tc.get("success") else "✗ Failed"
            summary = str(tc.get("input", {}))[:50] + "..."
            table.add_row(tc["tool"], status, summary)
        
        console.print(table)
    
    console.print(f"\n[dim]Iterations: {result['iterations']}[/dim]\n")


def interactive_mode(agent: GraphAgent):
    """Run the agent in interactive mode."""
    console.print(Panel(
        "[bold]Welcome to the Agentic Assistant[/bold]\n\n"
        "I can help you with:\n"
        "• Searching the knowledge base\n"
        "• Looking up policies\n"
        "• Finding employee information\n"
        "• Sending emails\n\n"
        "Type 'quit' or 'exit' to end the session.",
        title="🤖 Agent Ready",
        border_style="blue"
    ))
    
    while True:
        try:
            query = console.input("\n[bold cyan]You:[/bold cyan] ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['quit', 'exit', 'q']:
                console.print("[yellow]Goodbye![/yellow]")
                break
            
            with console.status("[bold green]Thinking...[/bold green]"):
                result = agent.invoke(query)
            
            display_response(result)
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Session interrupted.[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")


def single_query_mode(agent: GraphAgent, query: str):
    """Run a single query and exit."""
    with console.status("[bold green]Processing...[/bold green]"):
        result = agent.invoke(query)
    
    display_response(result)


def main():
    parser = argparse.ArgumentParser(description="Agentic Chatbot CLI")
    parser.add_argument(
        "-q", "--query",
        type=str,
        help="Single query to process (non-interactive mode)"
    )
    parser.add_argument(
        "-c", "--config",
        type=str,
        default="config/settings.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Initialize agent
    console.print("[dim]Initializing agent...[/dim]")
    agent = create_agent(config_path=args.config)
    
    if args.query:
        single_query_mode(agent, args.query)
    else:
        interactive_mode(agent)


if __name__ == "__main__":
    main()