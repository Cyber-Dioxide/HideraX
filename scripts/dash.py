from pycoin.symbols.dash import network as dash_network
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
import qrcode
import os
import json
import requests

console = Console()

WALLET_DIR = "wallet_DASH"
WALLET_NAME = "CyOX2_Dash_Wallet"
KEY_PATH = os.path.join(WALLET_DIR, "wallet_info.json")


def satoshis_to_dash(sats):
    return sats / 1e8


def wallet_exists():
    return os.path.exists(KEY_PATH)


def create_wallet():
    if wallet_exists():
        console.print("[yellow]⚠️ Wallet already exists. Use 'View Wallet' option instead.[/yellow]\n")
        return

    os.makedirs(WALLET_DIR, exist_ok=True)
    key = dash_network.keys.bip32_seed(os.urandom(32)).subkey_for_path("0/0")

    wallet_info = {
        "address": key.address(),
        "wif": key.wif(),
    }

    with open(KEY_PATH, "w") as f:
        json.dump(wallet_info, f, indent=4)

    console.print(Panel.fit(f"[green]✅ Wallet created successfully![/green]\n"
                            f"[bold cyan]Address:[/bold cyan] {key.address()}\n"
                            f"[bold cyan]Private Key (WIF):[/bold cyan] {key.wif()}",
                            title="New Dash Wallet Info"))


def view_wallet():
    if not wallet_exists():
        console.print("[red]❌ Wallet not found. Please create one first.[/red]\n")
        return

    with open(KEY_PATH) as f:
        info = json.load(f)

    address = info['address']
    wif = info['wif']

    # NOTE: DASH balance check API
    try:
        res = requests.get(f"https://api.blockcypher.com/v1/dash/main/addrs/{address}/balance")
        balance_sats = res.json().get("balance", 0)
    except:
        balance_sats = 0

    balance_dash = satoshis_to_dash(balance_sats)
    console.print(Panel.fit(f"[bold cyan]Wallet Address:[/bold cyan] {address}\n"
                            f"[bold cyan]Balance:[/bold cyan] {balance_dash:.8f} DASH\n"
                            f"[bold cyan]Private Key:[/bold cyan] {wif}",
                            title="[green]Wallet Info[/green]"))


def receive_dash():
    if not wallet_exists():
        console.print("[red]❌ Wallet not found.[/red]\n")
        return

    with open(KEY_PATH) as f:
        info = json.load(f)

    address = info['address']

    qr = qrcode.QRCode(border=1)
    qr.add_data(address)
    qr.make(fit=True)

    console.print(Panel.fit(f"[bold green]Your Dash Address:[/bold green]\n[cyan]{address}[/cyan]",
                            title="✅ [bold magenta]QR Code Info[/bold magenta]"))
    console.print("[bold light_green]Scan this QR code to receive DASH:[/bold light_green]\n")
    qr.print_ascii(invert=True)


def main_menu():
    while True:
        console.print(Panel("[bold yellow]Welcome to your DASH Wallet CLI[/bold yellow]",
                            subtitle="🔐 [green]Secure • Local • Simple[/green]", expand=False))

        if wallet_exists():
            console.print("[bold blue]1.[/bold blue] View Wallet")
        else:
            console.print("[bold blue]1.[/bold blue] Create Wallet")

        console.print("[bold blue]2.[/bold blue] Receive DASH")
        console.print("[bold blue]3.[/bold blue] Exit")

        choice = Prompt.ask("\n[bold green]Select an option[/bold green]", choices=["1", "2", "3"])

        if choice == "1":
            if wallet_exists():
                view_wallet()
            else:
                create_wallet()
        elif choice == "2":
            receive_dash()
        elif choice == "3":
            console.print("[bold red]Goodbye![/bold red]")
            break


if __name__ == "__main__":
    main_menu()
