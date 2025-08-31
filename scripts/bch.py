#!/usr/bin/env python3
"""
BCH CLI wallet using bitcash backend.
Features: create / view / receive (QR) / send
Stores wallet info in wallet_BCH/wallet_info.json
"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
import qrcode
import os
import json
from decimal import Decimal, ROUND_DOWN

# bitcash for BCH operations
from bitcash import Key
from bitcash.network import NetworkAPI

# ====== Config ======
console = Console()
COIN_TAG = "BCH"
WALLET_DIR = "wallet_BCH"
WALLET_NAME = "CyOX2_Wallet_BCH"
INFO_PATH = os.path.join(WALLET_DIR, "wallet_info.json")

# ====== Helpers ======
def satoshis_to_bch(sats: int) -> Decimal:
    if sats is None:
        return Decimal('0')
    return (Decimal(sats) / Decimal(1e8)).quantize(Decimal('0.00000001'))

def wallet_exists() -> bool:
    return os.path.exists(INFO_PATH)

def save_wallet_info(wif: str, address: str):
    os.makedirs(WALLET_DIR, exist_ok=True)
    wallet_info = {
        "wallet_name": WALLET_NAME,
        "address": address,
        "private_key_wif": wif,
        "note": "Store this file safely. Anyone with WIF can spend your BCH.",
    }
    with open(INFO_PATH, "w") as f:
        json.dump(wallet_info, f, indent=4)

def load_wallet_key() -> Key:
    """Return a bitcash.Key loaded from saved WIF."""
    if not wallet_exists():
        raise FileNotFoundError("Wallet info not found. Create wallet first.")
    with open(INFO_PATH, "r") as f:
        info = json.load(f)
    wif = info.get("private_key_wif")
    if not wif:
        raise ValueError("WIF missing from wallet info.")
    return Key(wif)

# ====== Core ======
def create_wallet():
    if wallet_exists():
        console.print("[yellow]⚠️ Wallet already exists. Use 'View Wallet' instead.[/yellow]\n")
        return

    # create new key
    key = Key()  # generates a new private key / address
    save_wallet_info(key.to_wif(), key.address)

    console.print(Panel.fit(
        f"[green]✅ {COIN_TAG} Wallet created![/green]\n"
        f"[bold cyan]Address:[/bold cyan] {key.address}\n"
        f"[bold cyan]Private Key (WIF):[/bold cyan] {key.to_wif()}",
        title=f"New {COIN_TAG} Wallet Info"
    ))

def view_wallet():
    if not wallet_exists():
        console.print("[red]❌ Wallet not found. Please create one first.[/red]\n")
        return

    try:
        key = load_wallet_key()
    except Exception as e:
        console.print(f"[red]❌ Failed to load wallet: {e}[/red]")
        return

    # Fetch balance using NetworkAPI (bitcash explorers)
    try:
        # bitcash Key.get_balance returns string; using NetworkAPI directly for satoshis help
        balance_bch = key.get_balance('bch')  # returns as string like '0.00000000'
        # normalize to Decimal
        balance_decimal = Decimal(balance_bch)
    except Exception as e:
        console.print(f"[yellow]⚠️ Could not fetch balance from network: {e}[/yellow]")
        balance_decimal = Decimal('0')

    console.print(Panel.fit(
        f"[bold cyan]{COIN_TAG} Wallet Address:[/bold cyan] {key.address}\n"
        f"[bold cyan]Balance:[/bold cyan] {balance_decimal:.8f} {COIN_TAG}\n"
        f"[bold cyan]Private Key (WIF):[/bold cyan] {key.to_wif()}",
        title=f"[green]{COIN_TAG} Wallet Info[/green]"
    ))

def receive_bch():
    if not wallet_exists():
        console.print("[red]❌ Wallet not found.[/red]\n")
        return

    try:
        key = load_wallet_key()
    except Exception as e:
        console.print(f"[red]❌ Failed to load wallet: {e}[/red]")
        return

    address = key.address

    table = Table(title=f"📥 Receive {COIN_TAG}", header_style="bold magenta")
    table.add_column("Index", style="cyan")
    table.add_column(f"{COIN_TAG} Address", style="green")
    table.add_row("1", address)
    console.print(table)

    console.print(Panel.fit(
        f"[bold green]Selected {COIN_TAG} Address:[/bold green]\n[cyan]{address}[/cyan]",
        title="✅ QR Code Info"
    ))
    console.print("[bold light_green]Scan this QR code to receive funds:[/bold light_green]\n")

    # show ASCII QR
    qr = qrcode.QRCode(border=1)
    qr.add_data(address)
    qr.make(fit=True)
    qr.print_ascii(invert=True)

def send_bch():
    if not wallet_exists():
        console.print("[red]❌ Wallet not found.[/red]\n")
        return

    try:
        key = load_wallet_key()
    except Exception as e:
        console.print(f"[red]❌ Failed to load wallet: {e}[/red]")
        return

    to_addr = Prompt.ask(f"[bold cyan]Enter recipient {COIN_TAG} address[/bold cyan]")

    try:
        # Amount in BCH -> Decimal
        amount_bch = Decimal(Prompt.ask(f"[bold cyan]Enter amount in {COIN_TAG}[/bold cyan]")).quantize(
            Decimal('0.00000001'), rounding=ROUND_DOWN
        )
        if amount_bch <= 0:
            raise ValueError("Amount must be positive.")
        # Convert to float for bitcash (bitcash expects decimal string or float)
        amount_for_send = float(amount_bch)

        # Fee input: allow empty to use default dynamic fee
        fee_input = Prompt.ask("[bold cyan]Enter desired fee in SATOSHIS (leave blank for auto)[/bold cyan]", default="")
        fee_arg = None
        if fee_input.strip() != "":
            try:
                fee_sats = int(fee_input)
                if fee_sats < 0:
                    raise ValueError("Fee must be >= 0")
                # bitcash accepts fee in satoshis via 'fee' kw param
                fee_arg = fee_sats
            except Exception as e:
                console.print(f"[red]❌ Invalid fee input: {e}[/red]")
                return
    except Exception as e:
        console.print(f"[red]❌ Invalid input. Reason: {e}[/red]\n")
        return

    console.print(Panel.fit(
        f"""[bold cyan]Debug Info[/bold cyan]
[blue]Recipient:[/blue] {to_addr}
[blue]Amount (BCH):[/blue] {amount_bch}
[blue]Fee (SATS - if set):[/blue] {fee_input or 'auto'}
""", title="🔍 Debug", border_style="yellow"))

    try:
        # Prepare outputs list for bitcash: (address, amount, 'bch')
        outputs = [(to_addr, amount_for_send, 'bch')]

        # If fee_arg is None, don't pass fee kwarg and let bitcash decide
        if fee_arg is None:
            txid = key.send(outputs)
        else:
            # bitcash's Key.send supports fee kw param (satoshis)
            txid = key.send(outputs, fee=fee_arg)

        console.print(Panel.fit(
            f"[green]✅ Transaction Sent![/green]\n[bold cyan]TXID:[/bold cyan] {txid}",
            title=f"{COIN_TAG} Transaction"
        ))

    except Exception as e:
        console.print(f"[bold red]❌ Error sending {COIN_TAG}:[/bold red] {e}")

def main_menu():
    while True:
        console.print(Panel(
            f"[bold yellow]Welcome to your {COIN_TAG} Wallet CLI[/bold yellow]",
            subtitle="🔐 [green]Secure • Local • Simple[/green]", expand=False
        ))

        if wallet_exists():
            console.print("[bold blue]1.[/bold blue] View Wallet")
        else:
            console.print("[bold blue]1.[/bold blue] Create Wallet")

        console.print(f"[bold blue]2.[/bold blue] Receive {COIN_TAG}")
        console.print(f"[bold blue]3.[/bold blue] Send {COIN_TAG}")
        console.print("[bold blue]4.[/bold blue] Exit")

        choice = Prompt.ask("\n[bold green]Select an option[/bold green]", choices=["1", "2", "3", "4"])
        if choice == "1":
            if wallet_exists():
                view_wallet()
            else:
                create_wallet()
        elif choice == "2":
            receive_bch()
        elif choice == "3":
            send_bch()
        elif choice == "4":
            console.print("[bold red]Goodbye![/bold red]")
            break

if __name__ == "__main__":
    main_menu()
