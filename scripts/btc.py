from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text
import qrcode
import os
import json
from bitcoinlib.wallets import Wallet
from bitcoinlib.services.services import Service
from bitcoinlib.transactions import Transaction
import requests

console = Console()
WALLET_DIR = "wallet_BTC"
WALLET_NAME = "CyOX2_Wallet"
DB_PATH = os.path.join(WALLET_DIR, f"{WALLET_NAME}.db")
INFO_PATH = os.path.join(WALLET_DIR, "wallet_info.json")


def satoshis_to_btc(sats):
    return sats / 1e8


def wallet_exists():
    return os.path.exists(DB_PATH)


def create_wallet():
    if wallet_exists():
        console.print("[yellow]⚠️ Wallet already exists. Use 'View Wallet' option instead.[/yellow]\n")
        return

    os.makedirs(WALLET_DIR, exist_ok=True)
    w = Wallet.create(WALLET_NAME, db_uri=f"sqlite:///{DB_PATH}")
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
                            title="New Wallet Info"))


def view_wallet():
    if not wallet_exists():
        console.print("[red]❌ Wallet not found. Please create one first.[/red]\n")
        return

    w = Wallet(WALLET_NAME, db_uri=f"sqlite:///{DB_PATH}")
    w.utxos_update()  # <-- Force update from network
    balance_sats = w.balance()
    balance_btc = satoshis_to_btc(balance_sats or 0)
    key = w.get_key()

    console.print(Panel.fit(f"[bold cyan]Wallet Address:[/bold cyan] {key.address}\n"
                            f"[bold cyan]Balance:[/bold cyan] {balance_btc:.8f} BTC\n"
                            f"[bold cyan]Private Key:[/bold cyan] {key.wif}",
                            title="[green]Wallet Info[/green]"))


def receive_btc():
    if not wallet_exists():
        console.print("[red]❌ Wallet not found.[/red]\n")
        return

    w = Wallet(WALLET_NAME, db_uri=f"sqlite:///{DB_PATH}")
    addresses = [w.get_key(i).address for i in range(3)]

    table = Table(title="📥 Receive BTC (Top 3 Addresses)", header_style="bold magenta")
    table.add_column("Index", style="cyan")
    table.add_column("BTC Address", style="green")

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

    console.print(Panel.fit(f"[bold green]Selected BTC Address:[/bold green]\n[cyan]{selected_address}[/cyan]",
                            title="✅ [bold magenta]QR Code Info[/bold magenta]"))

    console.print("[bold light_green]Scan this QR code to receive BTC:[/bold light_green]\n")
    qr.print_ascii(invert=True)


def get_btc_price_usdt():
    try:
        res = requests.get("https://api.coinbase.com/v2/prices/BTC-USDT/spot")
        data = res.json()
        return float(data['data']['amount'])
    except:
        return None


from decimal import Decimal, ROUND_DOWN

def send_btc():
    if not wallet_exists():
        console.print("[red]❌ Wallet not found.[/red]\n")
        return

    w = Wallet(WALLET_NAME, db_uri=f"sqlite:///{DB_PATH}")
    to_addr = Prompt.ask("[bold cyan]Enter recipient BTC address[/bold cyan]")

    try:
        # Amount in BTC, converted to satoshis
        amount_btc = Decimal(Prompt.ask("[bold cyan]Enter amount in BTC[/bold cyan]")).quantize(
            Decimal('0.00000001'), rounding=ROUND_DOWN)
        amount_sats = int(amount_btc * Decimal(1e8))

        # Fee directly in sats
        fee_sats = int(Prompt.ask("[bold cyan]Enter desired fee (in SATOSHIS)[/bold cyan]"))
    except Exception as e:
        console.print(f"[red]❌ Invalid input. Reason: {e}[/red]\n")
        return

    console.print(Panel.fit(
        f"""[bold cyan]Debug Info[/bold cyan]
[blue]Recipient:[/blue] {to_addr}
[blue]Amount (SATS):[/blue] {amount_sats}
[blue]Fee (SATS):[/blue] {fee_sats}
""", title="🔍 Debug", border_style="yellow"))

    try:
        # Finally send using output_arr (correct param name!)
        tx = w.send(
            output_arr=[(to_addr, amount_sats)],
            fee=fee_sats,
            replace_by_fee=True,
            broadcast=True  # Set to True to broadcast immediately
        )

        console.print(Panel.fit(f"[green]✅ Transaction Sent![/green]\n[bold cyan]TXID:[/bold cyan] {tx.txid}"))

        if fee_sats < 300:
            console.print("[yellow]⚠️ Low fee: May take hours to confirm.[/yellow]")
        elif fee_sats < 1000:
            console.print("[blue]⏳ Medium fee: ~30-60 minutes[/blue]")
        else:
            console.print("[bold green]🚀 High fee: Likely confirmed in ~10 minutes[/bold green]")

    except Exception as e:
        console.print(f"[bold red]❌ Error sending BTC:[/bold red] {e}")





def main_menu():
    while True:
        console.print(Panel("[bold yellow]Welcome to your BTC Wallet CLI[/bold yellow]",
                            subtitle="🔐 [green]Secure • Local • Simple[/green]", expand=False))

        if wallet_exists():
            console.print("[bold blue]1.[/bold blue] View Wallet")
        else:
            console.print("[bold blue]1.[/bold blue] Create Wallet")

        console.print("[bold blue]2.[/bold blue] Receive BTC")
        console.print("[bold blue]3.[/bold blue] Send BTC")
        console.print("[bold blue]4.[/bold blue] Exit")

        valid_choices = ["1", "2", "3", "4"]
        choice = Prompt.ask("\n[bold green]Select an option[/bold green]", choices=valid_choices)

        if choice == "1":
            if wallet_exists():
                view_wallet()
            else:
                create_wallet()
        elif choice == "2":
            receive_btc()
        elif choice == "3":
            send_btc()
        elif choice == "4":
            console.print("[bold red]Goodbye![/bold red]")
            break


if __name__ == "__main__":
    main_menu()
