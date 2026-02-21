"""
╔══════════════════════════════════════════════════════════════╗
║              🤖 KAZUHA VIP DISCORD AUTO BOT                  ║
║                  Created by Kazuha VIP Only                  ║
╚══════════════════════════════════════════════════════════════╝
Logging System Module
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from datetime import datetime
from typing import Optional


class Logger:
    """Rich console logging with beautiful formatting"""
    
    def __init__(self):
        self.console = Console()
        
    def banner(self):
        """Display the bot banner"""
        banner_text = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     ██╗  ██╗ █████╗ ███████╗██╗   ██╗██╗  ██╗ █████╗     ██╗   ██╗██╗██████╗ ║
║     ██║ ██╔╝██╔══██╗╚══███╔╝██║   ██║██║  ██║██╔══██╗    ██║   ██║██║██╔══██╗║
║     █████╔╝ ███████║  ███╔╝ ██║   ██║███████║███████║    ██║   ██║██║██████╔╝║
║     ██╔═██╗ ██╔══██║ ███╔╝  ██║   ██║██╔══██║██╔══██║    ╚██╗ ██╔╝██║██╔═══╝ ║
║     ██║  ██╗██║  ██║███████╗╚██████╔╝██║  ██║██║  ██║     ╚████╔╝ ██║██║     ║
║     ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝      ╚═══╝  ╚═╝╚═╝     ║
║                                                                              ║
║                    🤖 DISCORD AUTO BOT - VIP EDITION 🤖                      ║
║                         Created by Kazuha VIP Only                           ║
║                              Version 1.0.0                                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        self.console.print(Text(banner_text, style="bold cyan"))
    
    def status_panel(self, accounts: int, api_keys: dict, features: list):
        """Display system status panel"""
        table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("📦 Accounts", str(accounts))
        table.add_row(
            "🔑 Groq API Keys", 
            f"{api_keys['total']} total ({api_keys['active']} active, {api_keys['blocked']} blocked)"
        )
        table.add_row("✨ Features", " | ".join(features))
        
        panel = Panel(
            table,
            title="[bold white]✓ System Status[/bold white]",
            border_style="green",
            box=box.ROUNDED
        )
        self.console.print(panel)
    
    def info(self, message: str, prefix: str = "ℹ"):
        """Log info message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.print(f"[dim]{timestamp}[/dim] [{prefix}] [white]{message}[/white]")
    
    def success(self, message: str):
        """Log success message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.print(f"[dim]{timestamp}[/dim] [bold green]✓[/bold green] [green]{message}[/green]")
    
    def warning(self, message: str):
        """Log warning message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.print(f"[dim]{timestamp}[/dim] [bold yellow]⚠[/bold yellow] [yellow]{message}[/yellow]")
    
    def error(self, message: str):
        """Log error message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.print(f"[dim]{timestamp}[/dim] [bold red]✗[/bold red] [red]{message}[/red]")
    
    def action(self, account: str, server: str, channel: str, action_lines: list):
        """Log an action with tree structure"""
        header = f"[bold cyan]{account}[/bold cyan] → [yellow]{server}[/yellow] → [magenta]#{channel}[/magenta]"
        
        lines = [f"┌─ {header}"]
        for line in action_lines[:-1]:
            lines.append(f"│ {line}")
        if action_lines:
            lines.append(f"└─ {action_lines[-1]}")
        
        self.console.print("\n".join(lines))
    
    def menu_header(self, title: str):
        """Display menu header"""
        self.console.print(f"\n[bold cyan]{'═' * 50}[/bold cyan]")
        self.console.print(f"[bold white]  {title}[/bold white]")
        self.console.print(f"[bold cyan]{'═' * 50}[/bold cyan]\n")