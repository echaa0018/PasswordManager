from client import api_client
from client.flows.create_vault import run_create_vault_flow
from client.flows.login_backup import run_backup_login
from client.flows.login_normal import run_normal_login
from client.flows.vault_ops import add_password, delete_password, edit_password
from client.state import SessionState
from client.ui.menu import show_entry_selector, show_main_menu, show_vault_menu
from client.ui.prompts import (
    confirm_action,
    console,
    display_error,
    display_info,
    display_recovery_share,
    display_success,
    display_vault_entries,
    prompt_manual_password,
    prompt_master_password,
    prompt_password_choice,
    prompt_recovery_share,
    prompt_username,
)
from crypto.csprng import generate_password


def _handle_create() -> None:
    if not api_client.is_server_available():
        display_error("Server is unreachable. Vault creation requires the server.")
        return

    username = prompt_username()
    password = prompt_master_password(confirm=True)

    console.print("[dim]Creating vault (this takes a moment for key derivation)...[/dim]")
    success, recovery = run_create_vault_flow(username, password)

    if not success:
        display_error("Vault creation failed. The username may already exist.")
        return

    display_success(f"Vault created for '{username}'.")
    display_recovery_share(recovery)

    if confirm_action(
        "Also generate visual cryptography shares "
        "(2 PNG images that reveal a QR code only when physically stacked)?"
    ):
        _generate_visual_shares(recovery, username)


def _generate_visual_shares(recovery: str, username: str) -> None:
    try:
        from bonus.visual_crypto import (
            recovery_share_to_qr,
            save_shares,
            split_qr_visual,
        )
    except ImportError as exc:
        display_error(f"Visual crypto module unavailable: {exc}")
        return

    console.print("[dim]Building QR and splitting into visual cryptography shares...[/dim]")
    qr = recovery_share_to_qr(recovery)
    share1, share2 = split_qr_visual(qr)
    out_dir = f"data/client/vc_{username}"
    p1, p2 = save_shares(share1, share2, out_dir=out_dir)
    display_success(f"Wrote visual shares to:\n  {p1}\n  {p2}")
    console.print()
    console.print("[bold yellow]Recommended visual share handling:[/bold yellow]")
    console.print("[yellow]  1. Print both PNGs on paper or transparency sheets.[/yellow]")
    console.print("[yellow]  2. Store the two printouts in different physical locations[/yellow]")
    console.print("[yellow]     (e.g., one at home, one with a trusted person).[/yellow]")
    console.print("[yellow]  3. Delete the digital PNG files after printing, because keeping[/yellow]")
    console.print("[yellow]     both files together defeats the purpose of splitting.[/yellow]")
    console.print("[yellow]  4. To recover, physically overlay the two prints, scan the[/yellow]")
    console.print("[yellow]     resulting QR with any phone, then paste the decoded[/yellow]")
    console.print("[yellow]     string into Login (Backup) as your recovery share.[/yellow]")



def _handle_login_normal() -> SessionState | None:
    username = prompt_username()
    password = prompt_master_password()

    if not api_client.is_server_available():
        display_error("Server is unreachable.")
        if confirm_action("Try backup login (offline, read-only)?"):
            return _handle_login_backup_with_creds(username, password)
        return None

    console.print("[dim]Logging in...[/dim]")
    session = run_normal_login(username, password)
    if session is None:
        display_error("Login failed. Check username and master password.")
        return None

    display_success(f"Logged in as '{username}' (normal mode).")
    return session


def _handle_login_backup_with_creds(username: str, password: str) -> SessionState | None:
    recovery = prompt_recovery_share()
    if not recovery:
        display_error("Recovery share required.")
        return None

    console.print("[dim]Restoring vault from backup...[/dim]")
    session = run_backup_login(username, password, recovery)
    if session is None:
        display_error("Backup login failed. Check password and recovery share.")
        return None

    display_success(f"Logged in as '{username}' (backup / read-only).")
    return session


def _handle_login_backup() -> SessionState | None:
    username = prompt_username()
    password = prompt_master_password()
    return _handle_login_backup_with_creds(username, password)


def _handle_add(session: SessionState) -> None:
    service = console.input("[bold cyan]Service name: [/bold cyan]").strip()
    if not service:
        display_error("Service name required.")
        return
    username = console.input("[bold cyan]Account username: [/bold cyan]").strip()

    mode, length = prompt_password_choice()
    if mode == "manual":
        password = prompt_manual_password()
    else:
        password = generate_password(length)
        console.print(f"[dim]Generated password: [/dim][bold magenta]{password}[/bold magenta]")

    notes = console.input("[bold cyan]Notes (optional): [/bold cyan]").strip()

    if add_password(session, service, username, password, notes):
        display_success(f"Added entry for '{service}'.")
    else:
        display_error("Failed to add entry. Server may be unreachable.")


def _handle_edit(session: SessionState) -> None:
    entries = session.vault.list_entries()
    entry_id = show_entry_selector(entries)
    if entry_id is None:
        return

    current = session.vault.get_entry(entry_id)
    console.print(f"[dim]Editing '{current.service}'. Press Enter to keep current value.[/dim]")

    new_service = console.input(f"Service [{current.service}]: ").strip() or current.service
    new_username = console.input(f"Username [{current.username}]: ").strip() or current.username

    change_pw = confirm_action("Change password?")
    if change_pw:
        mode, length = prompt_password_choice()
        new_password = generate_password(length) if mode == "generate" else prompt_manual_password()
        if mode == "generate":
            console.print(f"[dim]New password: [/dim][bold magenta]{new_password}[/bold magenta]")
    else:
        new_password = current.password

    new_notes = console.input(f"Notes [{current.notes}]: ").strip() or current.notes

    if edit_password(
        session, entry_id,
        service=new_service, username=new_username,
        password=new_password, notes=new_notes,
    ):
        display_success("Entry updated.")
    else:
        display_error("Failed to update entry. Server may be unreachable.")


def _handle_delete(session: SessionState) -> None:
    entries = session.vault.list_entries()
    entry_id = show_entry_selector(entries)
    if entry_id is None:
        return

    target = session.vault.get_entry(entry_id)
    if not confirm_action(f"Permanently delete entry for '{target.service}'?"):
        display_info("Deletion cancelled.")
        return

    if delete_password(session, entry_id):
        display_success(f"Deleted '{target.service}'.")
    else:
        display_error("Failed to delete entry. Server may be unreachable.")


def _handle_reveal(session: SessionState) -> None:
    entries = session.vault.list_entries()
    entry_id = show_entry_selector(entries)
    if entry_id is None:
        return
    target = session.vault.get_entry(entry_id)
    console.print(f"[cyan]{target.service}[/cyan] / [green]{target.username}[/green]")
    console.print(f"[bold magenta]{target.password}[/bold magenta]")
    if target.notes:
        console.print(f"[dim]Notes:[/dim] {target.notes}")


def _vault_loop(session: SessionState) -> None:
    while True:
        action = show_vault_menu(read_only=session.is_read_only())
        if action == "list":
            display_vault_entries(session.vault.list_entries())
        elif action == "reveal":
            _handle_reveal(session)
        elif action == "add":
            _handle_add(session)
        elif action == "edit":
            _handle_edit(session)
        elif action == "delete":
            _handle_delete(session)
        elif action == "logout":
            session.clear()
            display_info("Logged out.")
            return


def main() -> None:
    console.print("[bold cyan]Distributed Password Manager (Shamir SSS)[/bold cyan]")

    while True:
        try:
            action = show_main_menu()
            if action == "quit":
                display_info("Goodbye.")
                return
            elif action == "create":
                _handle_create()
            elif action == "login_normal":
                session = _handle_login_normal()
                if session is not None:
                    _vault_loop(session)
            elif action == "login_backup":
                session = _handle_login_backup()
                if session is not None:
                    _vault_loop(session)
        except (KeyboardInterrupt, EOFError):
            console.print()
            display_info("Interrupted. Exiting.")
            return


if __name__ == "__main__":
    main()
