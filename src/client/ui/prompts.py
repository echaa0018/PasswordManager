from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

from client.vault import PasswordEntry

console = Console()


def prompt_username() -> str:
    while True:
        name = Prompt.ask("[bold cyan]Username[/bold cyan]").strip()
        if name:
            return name
        console.print("[red]Username cannot be empty.[/red]")


def prompt_master_password(confirm: bool = False) -> str:
    while True:
        pw = Prompt.ask("[bold cyan]Master password[/bold cyan]", password=True)
        if not pw:
            console.print("[red]Password cannot be empty.[/red]")
            continue
        if not confirm:
            return pw
        pw2 = Prompt.ask("[bold cyan]Confirm master password[/bold cyan]", password=True)
        if pw == pw2:
            return pw
        console.print("[red]Passwords do not match. Try again.[/red]")


def prompt_recovery_share() -> str:
    console.print("[dim]Paste the recovery share string (single line):[/dim]")
    return Prompt.ask("[bold cyan]Recovery share[/bold cyan]").strip()


def prompt_password_choice() -> tuple[str, int]:
    """Returns (mode, length). mode is 'manual' or 'generate'. length is 0 for manual."""
    mode = Prompt.ask(
        "Password source",
        choices=["manual", "generate"],
        default="generate",
    )
    if mode == "manual":
        return "manual", 0
    length = IntPrompt.ask("Length", default=20)
    if length < 4:
        length = 4
    return "generate", length


def prompt_manual_password() -> str:
    while True:
        pw = Prompt.ask("[bold cyan]Password[/bold cyan]", password=True)
        if pw:
            return pw
        console.print("[red]Password cannot be empty.[/red]")


def confirm_action(message: str) -> bool:
    return Confirm.ask(f"[yellow]{message}[/yellow]", default=False)


def display_recovery_share(share_str: str) -> None:
    panel = Panel.fit(
        f"[bold white]{share_str}[/bold white]\n\n"
        "[yellow]SAVE THIS RECOVERY SHARE NOW.[/yellow]\n"
        "[yellow]It will not be shown again. Without it, you cannot recover "
        "your vault if the server is unavailable.[/yellow]",
        title="[bold red]Recovery Share[/bold red]",
        border_style="yellow",
    )
    console.print(panel)


def display_error(msg: str) -> None:
    console.print(f"[bold red]Error:[/bold red] {msg}")


def display_success(msg: str) -> None:
    console.print(f"[bold green]✓[/bold green] {msg}")


def display_info(msg: str) -> None:
    console.print(f"[cyan]{msg}[/cyan]")


def display_vault_entries(entries: list[PasswordEntry], reveal: bool = False) -> None:
    if not entries:
        console.print("[dim](vault is empty)[/dim]")
        return

    table = Table(title="Vault Entries", show_lines=False)
    table.add_column("#", style="dim", width=3)
    table.add_column("Service", style="cyan")
    table.add_column("Username", style="green")
    table.add_column("Password", style="magenta")
    table.add_column("Notes", style="white")

    for i, entry in enumerate(entries, start=1):
        password_display = entry.password if reveal else "•" * 8
        table.add_row(str(i), entry.service, entry.username, password_display, entry.notes)

    console.print(table)