import qrcode
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from web3 import Web3
from eth_account import Account
import os
import json
import requests

console = Console()

# Use a public RPC or your own BSC node
BSC_RPC = "https://bsc-dataseed.binance.org/"
web3 = Web3(Web3.HTTPProvider(BSC_RPC))

WALLET_DIR = "wallet_BNB"
WALLET_NAME = "CyOX2_BNB"
INFO_PATH = os.path.join(WALLET_DIR, "wallet_info.json")


def wallet_exists():
    return os.path.exists(INFO_PATH)


def create_wallet():
    if wallet_exists():
        console.print("[yellow]⚠️ Wallet already exists. Use 'View Wallet' instead.[/yellow]\n")
        return

    acct = Account.create()
    os.makedirs(WALLET_DIR, exist_ok=True)

    wallet_info = {
        "address": acct.address,
        "private_key": acct.key.hex()
    }

    with open(INFO_PATH, "w") as f:
        json.dump(wallet_info, f, indent=4)

    console.print(Panel.fit(f"[green]✅ BNB Wallet Created![/green]\n"
                            f"[bold cyan]Address:[/bold cyan] {acct.address}\n"
                            f"[bold cyan]Private Key:[/bold cyan] {acct.key.hex()}",
                            title="New BNB Wallet"))


def load_wallet():
    if not wallet_exists():
        return None
    with open(INFO_PATH, "r") as f:
        return json.load(f)


def view_wallet():
    wallet = load_wallet()
    if not wallet:
        console.print("[red]❌ Wallet not found.[/red]\n")
        return

    address = wallet['address']
    balance_wei = web3.eth.get_balance(address)
    balance_bnb = web3.from_wei(balance_wei, 'ether')

    console.print(Panel.fit(f"[bold cyan]Address:[/bold cyan] {address}\n"
                            f"[bold cyan]Balance:[/bold cyan] {balance_bnb:.6f} BNB\n"
                            f"[bold cyan]Private Key:[/bold cyan] {wallet['private_key']}",
                            title="[green]BNB Wallet Info[/green]"))


def receive_bnb():
    wallet = load_wallet()
    if not wallet:
        console.print("[red]❌ Wallet not found.[/red]\n")
        return

    address = wallet["address"]

    table = Table(title="📥 Receive BNB", header_style="bold magenta")
    table.add_column("Network", style="cyan")
    table.add_column("Address", style="green")
    table.add_row("BNB Smart Chain", address)
    console.print(table)

    console.print("[bold green]Scan this QR to receive BNB:[/bold green]")
    qr = qrcode.QRCode(border=1)
    qr.add_data(address)
    qr.make(fit=True)
    qr.print_ascii(invert=True)


def get_bnb_price_usdt():
    try:
        res = requests.get("https://api.coinbase.com/v2/prices/BNB-USDT/spot")
        return float(res.json()['data']['amount'])
    except:
        return None


def send_bnb():
    wallet = load_wallet()
    if not wallet:
        console.print("[red]❌ Wallet not found.[/red]\n")
        return

    to_address = Prompt.ask("[bold cyan]Enter recipient BNB address[/bold cyan]")
    amount = float(Prompt.ask("[bold cyan]Enter amount in BNB[/bold cyan]"))
    fee_usdt = float(Prompt.ask("[bold cyan]Enter desired fee in USDT[/bold cyan]"))

    bnb_price = get_bnb_price_usdt()
    if bnb_price is None:
        console.print("[red]❌ Failed to fetch BNB price.[/red]")
        return

    gas_price_gwei = int((fee_usdt / bnb_price) / 0.000021 * 1e9)
    gas_price_wei = web3.to_wei(gas_price_gwei, 'gwei')

    try:
        nonce = web3.eth.get_transaction_count(wallet['address'])
        tx = {
            'to': to_address,
            'value': web3.to_wei(amount, 'ether'),
            'gas': 21000,
            'gasPrice': gas_price_wei,
            'nonce': nonce,
            'chainId': 56  # BSC chain ID
        }

        signed_tx = web3.eth.account.sign_transaction(tx, private_key=wallet['private_key'])
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

        console.print(Panel.fit(f"[green]✅ Transaction Sent[/green]\n[bold cyan]TX Hash:[/bold cyan] {tx_hash.hex()}"))

        if fee_usdt < 0.5:
            console.print("[yellow]⚠️ Low fee: May delay confirmation[/yellow]")
        elif fee_usdt < 1.5:
            console.print("[blue]⏳ Medium fee: ~1-3 mins[/blue]")
        else:
            console.print("[bold green]🚀 High fee: Likely confirmed quickly[/bold green]")
    except Exception as e:
        console.print(f"[red]❌ Error sending BNB:[/red] {e}")


def main_menu():
    while True:
        console.print(Panel("[bold yellow]Welcome to your BNB Wallet CLI[/bold yellow]",
                            subtitle="🔐 [green]Secure • Local • Simple[/green]", expand=False))

        if wallet_exists():
            console.print("[bold blue]1.[/bold blue] View Wallet")
        else:
            console.print("[bold blue]1.[/bold blue] Create Wallet")

        console.print("[bold blue]2.[/bold blue] Receive BNB")
        console.print("[bold blue]3.[/bold blue] Send BNB")
        console.print("[bold blue]4.[/bold blue] Exit")

        choice = Prompt.ask("\n[bold green]Select an option[/bold green]", choices=["1", "2", "3", "4"])

        if choice == "1":
            if wallet_exists():
                view_wallet()
            else:
                create_wallet()
        elif choice == "2":
            receive_bnb()
        elif choice == "3":
            send_bnb()
        elif choice == "4":
            console.print("[bold red]Goodbye![/bold red]")
            break


if __name__ == "__main__":
    main_menu()
