import os
import json
import base58
import requests
import qrcode
from nacl import signing
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

console = Console()

WALLET_DIR = "wallet_SOL"
WALLET_NAME = "CyOX2_SOL"
INFO_PATH = os.path.join(WALLET_DIR, "wallet_info.json")
RPC_URL = "https://api.mainnet-beta.solana.com"

def wallet_exists():
    return os.path.exists(INFO_PATH)

def create_wallet():
    if wallet_exists():
        console.print("[yellow]⚠️ Wallet already exists.[/yellow]\n")
        return

    os.makedirs(WALLET_DIR, exist_ok=True)

    # Generate new keypair
    key = signing.SigningKey.generate()
    secret_key = key.encode()
    public_key = key.verify_key.encode()

    address = base58.b58encode(public_key).decode()
    private_key = base58.b58encode(secret_key).decode()

    wallet_info = {
        "address": address,
        "private_key": private_key
    }

    with open(INFO_PATH, "w") as f:
        json.dump(wallet_info, f, indent=4)

    console.print(Panel.fit(f"[green]✅ SOL Wallet Created![/green]\n"
                            f"[bold cyan]Address:[/bold cyan] {address}\n"
                            f"[bold cyan]Private Key:[/bold cyan] {private_key}",
                            title="New Solana Wallet"))

def load_wallet():
    if not wallet_exists():
        return None
    with open(INFO_PATH, "r") as f:
        return json.load(f)

def get_sol_balance(address):
    headers = {"Content-Type": "application/json"}
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [address]
    }
    res = requests.post(RPC_URL, headers=headers, json=body)
    try:
        lamports = res.json()["result"]["value"]
        return lamports / 1e9
    except:
        return None

def view_wallet():
    wallet = load_wallet()
    if not wallet:
        console.print("[red]❌ Wallet not found.[/red]\n")
        return

    balance = get_sol_balance(wallet["address"])
    console.print(Panel.fit(f"[bold cyan]Address:[/bold cyan] {wallet['address']}\n"
                            f"[bold cyan]Balance:[/bold cyan] {balance:.6f} SOL\n"
                            f"[bold cyan]Private Key:[/bold cyan] {wallet['private_key']}",
                            title="[green]Solana Wallet Info[/green]"))

def receive_sol():
    wallet = load_wallet()
    if not wallet:
        console.print("[red]❌ Wallet not found.[/red]\n")
        return

    address = wallet["address"]
    table = Table(title="📥 Receive SOL", header_style="bold magenta")
    table.add_column("Network", style="cyan")
    table.add_column("Address", style="green")
    table.add_row("Solana Mainnet", address)
    console.print(table)

    console.print("[bold green]Scan this QR to receive SOL:[/bold green]")
    qr = qrcode.QRCode(border=1)
    qr.add_data(address)
    qr.make(fit=True)
    qr.print_ascii(invert=True)

def main_menu():
    while True:
        console.print(Panel("[bold yellow]Welcome to your SOL Wallet CLI[/bold yellow]",
                            subtitle="🔐 [green]Secure • Local • Simple[/green]", expand=False))

        if wallet_exists():
            console.print("[bold blue]1.[/bold blue] View Wallet")
        else:
            console.print("[bold blue]1.[/bold blue] Create Wallet")

        console.print("[bold blue]2.[/bold blue] Receive SOL")
        console.print("[bold blue]3.[/bold blue] Exit")

        choice = Prompt.ask("\n[bold green]Select an option[/bold green]", choices=["1", "2", "3"])

        if choice == "1":
            if wallet_exists():
                view_wallet()
            else:
                create_wallet()
        elif choice == "2":
            receive_sol()
        elif choice == "3":
            console.print("[bold red]Goodbye![/bold red]")
            break

if __name__ == "__main__":
    main_menu()
