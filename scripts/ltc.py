from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
import qrcode
import os
import json
from bitcoinlib.wallets import Wallet
from bitcoinlib.transactions import Transaction
import requests

console = Console()
WALLET_DIR = "wallet_LTC"
WALLET_NAME = "CyOX2_LTC_Wallet"
DB_PATH = os.path.join(WALLET_DIR, f"{WALLET_NAME}.db")
INFO_PATH = os.path.join(WALLET_DIR, "wallet_info.json")


def litoshis_to_ltc(litoshis):
    return litoshis / 1e8


def wallet_exists():
    return os.path.exists(DB_PATH)


def create_wallet():
    if wallet_exists():
        console.print("[yellow]⚠️ Wallet already exists. Use 'View Wallet' option instead.[/yellow]\n")
        return

    os.makedirs(WALLET_DIR, exist_ok=True)
    w = Wallet.create(WALLET_NAME, db_uri=f"sqlite:///{DB_PATH}", network='litecoin')
    key = w.get_key()

    wallet_info = {
        "wallet_name": WALLET_NAME,
        "address": key.address,
        "private_key_wif": key.wif,
    }

    with open(INFO_PATH, "w") as f:
        json.dump(wallet_info, f, indent=4)

    console.print(Panel.fit(f"[green]✅ Wallet created successfully![/green]\n"
                            f"[bold cyan]Address:[/bold cyan] {key.address}\n"
                            f"[bold cyan]Private Key:[/bold cyan] {key.wif}",
                            title="New Litecoin Wallet Info"))


def view_wallet():
    if not wallet_exists():
        console.print("[red]❌ Wallet not found. Please create one first.[/red]\n")
        return
    w = Wallet(WALLET_NAME, db_uri=f"sqlite:///{DB_PATH}")

    balance_litoshis = w.balance()
    balance_ltc = litoshis_to_ltc(balance_litoshis or 0)
    key = w.get_key()
    console.print(Panel.fit(f"[bold cyan]Wallet Address:[/bold cyan] {key.address}\n"
                            f"[bold cyan]Balance:[/bold cyan] {balance_ltc:.8f} LTC\n"
                            f"[bold cyan]Private Key:[/bold cyan] {key.wif}",
                            title="[green]Litecoin Wallet Info[/green]"))


def receive_ltc():
    if not wallet_exists():
        console.print("[red]❌ Wallet not found.[/red]\n")
        return

    w = Wallet(WALLET_NAME, db_uri=f"sqlite:///{DB_PATH}")

    addresses = [w.get_key(i).address for i in range(3)]

    table = Table(title="📥 Receive LTC (Top 3 Addresses)", header_style="bold magenta")
    table.add_column("Index", style="cyan")
    table.add_column("LTC Address", style="green")

    for idx, addr in enumerate(addresses):
        table.add_row(str(idx + 1), addr)

    console.print(table)

    choice = Prompt.ask("[bold yellow]Enter the index (1-3) of the address to generate QR[/bold yellow]",
                        choices=["1", "2", "3"], default="1")

    selected_address = addresses[int(choice) - 1]

    # Generate and display QR code
    qr = qrcode.QRCode(border=1)
    qr.add_data(selected_address)
    qr.make(fit=True)

    console.print(Panel.fit(f"[bold green]Selected LTC Address:[/bold green]\n[cyan]{selected_address}[/cyan]",
                            title="✅ [bold magenta]QR Code Info[/bold magenta]"))

    console.print("[bold light_green]Scan this QR code to receive LTC:[/bold light_green]\n")
    qr.print_ascii(invert=True)


def get_ltc_price_usdt():
    try:
        res = requests.get("https://api.coinbase.com/v2/prices/LTC-USDT/spot")
        data = res.json()
        return float(data['data']['amount'])
    except:
        return None


def send_ltc():
    if not wallet_exists():
        console.print("[red]❌ Wallet not found.[/red]\n")
        return

    w = Wallet(WALLET_NAME, db_uri=f"sqlite:///{DB_PATH}")

    to_addr = Prompt.ask("[bold cyan]Enter recipient LTC address[/bold cyan]")
    amount_ltc = float(Prompt.ask("[bold cyan]Enter amount in LTC[/bold cyan]"))
    fee_usdt = float(Prompt.ask("[bold cyan]Enter desired fee (in USDT)[/bold cyan]"))

    ltc_price = get_ltc_price_usdt()
    if ltc_price is None:
        console.print("[red]❌ Could not fetch LTC price from API.[/red]\n")
        return

    fee_ltc = fee_usdt / ltc_price
    fee_litoshis = int(fee_ltc * 1e8)

    try:
        tx = w.send_to(to_addr, amount_ltc, fee=fee_litoshis, offline=False, replace_by_fee=True)
        console.print(Panel.fit(f"[green]✅ Transaction Sent![/green]\n[bold cyan]TXID:[/bold cyan] {tx.txid}"))

        if fee_usdt < 0.1:
            console.print("[yellow]⚠️ Low fee: May take longer to confirm.[/yellow]")
        elif fee_usdt < 0.5:
            console.print("[blue]⏳ Medium fee: ~10-30 minutes[/blue]")
        else:
            console.print("[bold green]🚀 High fee: Likely confirmed quickly[/bold green]")
        console.print()
    except Exception as e:
        console.print(f"[red]❌ Error sending LTC:[/red] {e}\n")


def main_menu():
    while True:
        console.print(Panel("[bold yellow]Welcome to your LTC Wallet CLI[/bold yellow]",
                            subtitle="🔐 [green]Secure • Local • Simple[/green]", expand=False))

        if wallet_exists():
            console.print("[bold blue]1.[/bold blue] View Wallet")
        else:
            console.print("[bold blue]1.[/bold blue] Create Wallet")

        console.print("[bold blue]2.[/bold blue] Receive LTC")
        console.print("[bold blue]3.[/bold blue] Send LTC")
        console.print("[bold blue]4.[/bold blue] Exit")

        valid_choices = ["1", "2", "3", "4"]
        choice = Prompt.ask("\n[bold green]Select an option[/bold green]", choices=valid_choices)

        if choice == "1":
            if wallet_exists():
                view_wallet()
            else:
                create_wallet()
        elif choice == "2":
            receive_ltc()
        elif choice == "3":
            send_ltc()
        elif choice == "4":
            console.print("[bold red]Goodbye![/bold red]")
            break


if __name__ == "__main__":
    main_menu()
