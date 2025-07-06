from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
import qrcode
import os
import json
from pycoin.symbols.zec import network

console = Console()
WALLET_DIR = "wallet_ZEC"
WALLET_NAME = "CyOX2_ZEC_Wallet"
INFO_PATH = os.path.join(WALLET_DIR, "wallet_info.json")


def wallet_exists():
    return os.path.exists(INFO_PATH)


def create_wallet():
    if wallet_exists():
        console.print("[yellow]⚠️ Wallet already exists. Use 'View Wallet' instead.[/yellow]")
        return

    os.makedirs(WALLET_DIR, exist_ok=True)
    key = network.keys.bip32_seed(os.urandom(32))

    wallet_info = {
        "address": key.address(),
        "wif": key.wif(),
    }

    with open(INFO_PATH, "w") as f:
        json.dump(wallet_info, f, indent=4)

    console.print(Panel.fit(f"[green]✅ Wallet created successfully![/green]\n"
                            f"[bold cyan]Address:[/bold cyan] {wallet_info['address']}\n"
                            f"[bold cyan]Private Key (WIF):[/bold cyan] {wallet_info['wif']}",
                            title="🪙 New ZEC Wallet Info"))


def view_wallet():
    if not wallet_exists():
        console.print("[red]❌ Wallet not found. Please create one first.[/red]")
        return

    with open(INFO_PATH, "r") as f:
        data = json.load(f)

    console.print(Panel.fit(f"[bold cyan]ZEC Address:[/bold cyan] {data['address']}\n"
                            f"[bold cyan]Private Key (WIF):[/bold cyan] {data['wif']}",
                            title="👛 Wallet Info"))


def receive_zec():
    if not wallet_exists():
        console.print("[red]❌ Wallet not found.[/red]")
        return

    with open(INFO_PATH, "r") as f:
        data = json.load(f)

    address = data["address"]

    # Generate QR code
    qr = qrcode.QRCode(border=1)
    qr.add_data(address)
    qr.make(fit=True)

    console.print(Panel.fit(f"[bold green]Scan this QR to receive ZEC:[/bold green]\n[cyan]{address}[/cyan]",
                            title="✅ QR Code Info"))
    qr.print_ascii(invert=True)


def main_menu():
    while True:
        console.print(Panel("[bold yellow]ZEC Wallet CLI[/bold yellow]",
                            subtitle="🔐 [green]Secure • Local • Transparent Addresses[/green]", expand=False))

        console.print("[bold blue]1.[/bold blue] Create/View Wallet")
        console.print("[bold blue]2.[/bold blue] Receive ZEC")
        console.print("[bold blue]3.[/bold blue] Exit")

        choice = Prompt.ask("\n[bold green]Select an option[/bold green]", choices=["1", "2", "3"])

        if choice == "1":
            view_wallet() if wallet_exists() else create_wallet()
        elif choice == "2":
            receive_zec()
        elif choice == "3":
            console.print("[bold red]Goodbye![/bold red]")
            break


if __name__ == "__main__":
    main_menu()
