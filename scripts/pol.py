import qrcode
from web3 import Web3, Account
from eth_account.messages import encode_defunct
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
import os
import json

console = Console()

# === Configuration ===
INFURA_PROJECT_ID = "ae6132a817bc4f029109a313dd848182"
POLYGON_RPC = f"https://polygon-mainnet.infura.io/v3/{INFURA_PROJECT_ID}"
WALLET_DIR = "wallet_POL"
WALLET_FILE = os.path.join(WALLET_DIR, "wallet.json")

w3 = Web3(Web3.HTTPProvider(POLYGON_RPC))


def create_wallet():
    if os.path.exists(WALLET_FILE):
        console.print("[yellow]Wallet already exists. Use 'View Wallet' instead.[/yellow]")
        return

    os.makedirs(WALLET_DIR, exist_ok=True)
    acct = Account.create()

    # Save private key to local JSON file
    wallet_data = {
        "address": acct.address,
        "private_key": acct._private_key.hex()
    }

    with open(WALLET_FILE, "w") as f:
        json.dump(wallet_data, f, indent=4)

    console.print(
        Panel.fit(f"[green]Wallet Created Successfully![/green]\nAddress: [bold cyan]{acct.address}[/bold cyan]"))


def load_wallet():
    if not os.path.exists(WALLET_FILE):
        console.print("[red]Wallet not found. Please create a wallet first.[/red]")
        return None

    with open(WALLET_FILE, "r") as f:
        data = json.load(f)
    return data


def view_wallet():
    wallet = load_wallet()
    if not wallet:
        return
    address = wallet['address']
    private_key = wallet['private_key']
    balance = w3.eth.get_balance(address)
    balance_matic = w3.from_wei(balance, 'ether')

    console.print(Panel.fit(f"[bold cyan]Wallet Address:[/bold cyan] {address}\n"
                            f"[bold cyan]Balance:[/bold cyan] {balance_matic} MATIC\n"
                            f"[bold cyan]Private Key:[/bold cyan] {private_key}",
                            title="[green]Wallet Info[/green]"))


def receive_matic():
    wallet = load_wallet()
    if not wallet:
        console.print("[red]❌ Wallet not found.[/red]\n")
        return

    address = wallet['address']

    console.print(Panel.fit(f"[bold cyan]Receive MATIC Address:[/bold cyan]\n{address}",
                            title="📥 [magenta]MATIC Wallet[/magenta]"))

    # Display QR code
    console.print("[bold green]Scan this QR to receive MATIC:[/bold green]")
    qr = qrcode.QRCode(border=1)
    qr.add_data(address)
    qr.make(fit=True)
    qr.print_ascii(invert=True)


def send_matic():
    wallet = load_wallet()
    if not wallet:
        return

    to_address = Prompt.ask("[bold cyan]Enter recipient address[/bold cyan]")
    amount = float(Prompt.ask("[bold cyan]Enter amount to send (MATIC)[/bold cyan]"))
    gas_price_gwei = float(Prompt.ask("[bold cyan]Enter gas price (Gwei)[/bold cyan]"))

    private_key = wallet['private_key']
    sender_address = wallet['address']

    nonce = w3.eth.get_transaction_count(sender_address)
    gas_price = w3.toWei(gas_price_gwei, 'gwei')

    tx = {
        'nonce': nonce,
        'to': to_address,
        'value': w3.toWei(amount, 'ether'),
        'gas': 21000,
        'gasPrice': gas_price,
        'chainId': 137  # Polygon Mainnet Chain ID
    }

    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    try:
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        console.print(Panel.fit(f"[green]Transaction sent![/green]\nTx hash: [bold]{tx_hash.hex()}[/bold]"))
    except Exception as e:
        console.print(f"[red]Error sending transaction:[/red] {e}")


def main_menu():
    while True:
        console.print(Panel("[bold yellow]Polygon (MATIC) Wallet CLI[/bold yellow]",
                            subtitle="Powered by Web3.py & Infura", expand=False))
        wallet_exists = os.path.exists(WALLET_FILE)

        console.print("[bold blue]1.[/bold blue] " + ("View Wallet" if wallet_exists else "Create Wallet"))
        console.print("[bold blue]2.[/bold blue] Receive MATIC")
        console.print("[bold blue]3.[/bold blue] Send MATIC")
        console.print("[bold blue]4.[/bold blue] Exit")

        choice = Prompt.ask("\n[bold green]Select an option[/bold green]", choices=["1", "2", "3", "4"])

        if choice == "1":
            if wallet_exists:
                view_wallet()
            else:
                create_wallet()
        elif choice == "2":
            receive_matic()
        elif choice == "3":
            send_matic()
        elif choice == "4":
            console.print("[bold red]Goodbye![/bold red]")
            break


if __name__ == "__main__":
    main_menu()
