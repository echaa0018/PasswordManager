from rich.console import Console
from rich.prompt import Prompt
from client.vault import PasswordEntry

console = Console()


def show_main_menu() -> str:
    console.print()
    console.print("[bold cyan]═══ Password Manager ═══[/bold cyan]")
    console.print("  [bold]1[/bold]) Create vault")
    console.print("  [bold]2[/bold]) Login (Normal)")
    console.print("  [bold]3[/bold]) Login (Backup)")
    console.print("  [bold]4[/bold]) Quit")
    choice = Prompt.ask("Choose", choices=["1", "2", "3", "4"], default="2")
    return {
        "1": "create",
        "2": "login_normal",
        "3": "login_backup",
        "4": "quit",
    }[choice]


def show_vault_menu(read_only: bool = False) -> str:
    console.print()
    mode = "[yellow](READ-ONLY backup mode)[/yellow]" if read_only else "[green](normal mode)[/green]"
    console.print(f"[bold cyan]═══ Vault Menu ═══[/bold cyan] {mode}")
    console.print("  [bold]1[/bold]) List entries")
    console.print("  [bold]2[/bold]) Reveal entry password")
    if not read_only:
        console.print("  [bold]3[/bold]) Add entry")
        console.print("  [bold]4[/bold]) Edit entry")
        console.print("  [bold]5[/bold]) Delete entry")
    console.print("  [bold]6[/bold]) Logout")

    choices = ["1", "2", "6"] if read_only else ["1", "2", "3", "4", "5", "6"]
    choice = Prompt.ask("Choose", choices=choices, default="1")
    return {
        "1": "list",
        "2": "reveal",
        "3": "add",
        "4": "edit",
        "5": "delete",
        "6": "logout",
    }[choice]


def show_entry_selector(entries: list[PasswordEntry]) -> str | None:
    if not entries:
        console.print("[dim](no entries to select)[/dim]")
        return None

    console.print()
    for i, entry in enumerate(entries, start=1):
        console.print(f"  [bold]{i}[/bold]) [cyan]{entry.service}[/cyan] — {entry.username}")
    console.print("  [bold]0[/bold]) Cancel")

    valid = [str(i) for i in range(0, len(entries) + 1)]
    choice = Prompt.ask("Select entry", choices=valid, default="0")
    if choice == "0":
        return None
    return entries[int(choice) - 1].id