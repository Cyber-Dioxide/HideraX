from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
import os
import json
import qrcode

from monero.seed import Seed

console = Console()
WALLET_DIR = "wallet_XMR"
INFO_PATH = os.path.join(WALLET_DIR, "wallet_info.json")


def wallet_exists():
    return os.path.exists(INFO_PATH)


def create_wallet():
    if wallet_exists():
        console.print("[yellow]⚠️ Wallet already exists. Use 'View Wallet' instead.[/yellow]\n")
        return

    os.makedirs(WALLET_DIR, exist_ok=True)
    seed = Seed()

    info = {
        "mnemonic": seed.phrase,
        "address": str(seed.public_address()),
        "private_spend_key": seed.secret_spend_key(),
        "private_view_key": seed.secret_view_key()
    }

    with open(INFO_PATH, "w") as f:
        json.dump(info, f, indent=4)

    console.print(Panel.fit(
        f"[green]✅ XMR Wallet Created![/green]\n"
        f"[bold cyan]Mnemonic:[/bold cyan] {info['mnemonic']}\n"
        f"[bold cyan]Address:[/bold cyan] {info['address']}\n"
        f"[bold cyan]Spend Key:[/bold cyan] {info['private_spend_key']}\n"
        f"[bold cyan]View Key:[/bold cyan] {info['private_view_key']}",
        title="🛡️ New Monero Wallet"))


def view_wallet():
    if not wallet_exists():
        console.print("[red]❌ Wallet not found. Please create one first.[/red]\n")
        return
    with open(INFO_PATH) as f:
        info = json.load(f)

    console.print(Panel.fit(f"[bold cyan]Mnemonic:[/bold cyan] {info['mnemonic']}\n"
                            f"[bold cyan]Address:[/bold cyan] {info['address']}\n"
                            f"[bold cyan]Spend Key:[/bold cyan] {info['private_spend_key']}\n"
                            f"[bold cyan]View Key:[/bold cyan] {info['private_view_key']}",
                            title="🛡️ Monero Wallet Info"))


def receive_xmr():
    if not wallet_exists():
        console.print("[red]❌ Wallet not found.[/red]\n")
        return
    with open(INFO_PATH) as f:
        info = json.load(f)

    addr = info["address"]
    console.print(Panel.fit(f"[bold green]Scan this QR to receive XMR:[/bold green]\n[cyan]{addr}[/cyan]",
                            title="✅ Receive Monero"))
    q = qrcode.QRCode(border=1)
    q.add_data(addr)
    q.make(fit=True)
    q.print_ascii(invert=True)


def main_menu():
    while True:
        console.print(Panel("[bold yellow]XMR Wallet CLI[/bold yellow]",
                            subtitle="🔐 Offline-Only • Private • Local", expand=False))

        if wallet_exists():
            console.print("[bold blue]1.[/bold blue] View Wallet")
        else:
            console.print("[bold blue]1.[/bold blue] Create Wallet")

        console.print("[bold blue]2.[/bold blue] Receive XMR")
        console.print("[bold blue]3.[/bold blue] Exit")
        choice = Prompt.ask("\n[bold green]Select an option[/bold green]", choices=["1", "2", "3"])
        if choice == "1":
            view_wallet() if wallet_exists() else create_wallet()
        elif choice == "2":
            receive_xmr()
        else:
            console.print("[bold red]Goodbye![/bold red]")
            break


if __name__ == "__main__":
    main_menu()
