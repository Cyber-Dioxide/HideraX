from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
import qrcode
import os
import json
from bitcoinlib.wallets import Wallet
import requests

console = Console()
WALLET_DIR = "wallet_DOGE"
WALLET_NAME = "CyOX2_DOGE_Wallet"
DB_PATH = os.path.join(WALLET_DIR, f"{WALLET_NAME}.db")
INFO_PATH = os.path.join(WALLET_DIR, "wallet_info.json")


def dogetoshis_to_doge(sats):
    return sats / 1e8


def wallet_exists():
    return os.path.exists(DB_PATH)


def create_wallet():
    if wallet_exists():
        console.print("[yellow]⚠️ Wallet already exists. Use 'View Wallet' instead.[/yellow]\n")
        return

    os.makedirs(WALLET_DIR, exist_ok=True)
    w = Wallet.create(
        WALLET_NAME,
        db_uri=f"sqlite:///{DB_PATH}",
        network='dogecoin',
        witness_type='legacy'  # 👈 Force legacy for DOGE
    )
    key = w.get_key()
    info = {"wallet_name": WALLET_NAME, "address": key.address, "private_key_wif": key.wif}
    with open(INFO_PATH, "w") as f:
        json.dump(info, f, indent=4)
    console.print(Panel.fit(f"[green]✅ Wallet created![/green]\n[cyan]Address:[/cyan] {key.address}\n[cyan]WIF:[/cyan] {key.wif}",
                            title="New DOGE Wallet Info"))


def view_wallet():
    if not wallet_exists():
        console.print("[red]❌ No wallet found. Please create one.[/red]\n")
        return
    w = Wallet(WALLET_NAME, db_uri=f"sqlite:///{DB_PATH}")
    bal = w.balance() or 0
    console.print(Panel.fit(f"[cyan]Address:[/cyan] {w.get_key().address}\n"
                            f"[cyan]Balance:[/cyan] {dogetoshis_to_doge(bal):.8f} DOGE\n"
                            f"[cyan]WIF:[/cyan] {w.get_key().wif}",
                            title="[green]DOGE Wallet Info[/green]"))


def receive_doge():
    if not wallet_exists():
        console.print("[red]❌ No wallet found.[/red]\n"); return
    w = Wallet(WALLET_NAME, db_uri=f"sqlite:///{DB_PATH}")
    addrs = [w.get_key(i).address for i in range(3)]
    table = Table(title="Receive DOGE (Top 3 Addresses)", header_style="magenta")
    table.add_column("Index"); table.add_column("DOGE Address")
    for i, a in enumerate(addrs, 1): table.add_row(str(i), a)
    console.print(table)
    choice = Prompt.ask("Choose address index", choices=["1", "2", "3"], default="1")
    addr = addrs[int(choice)-1]
    qr = qrcode.QRCode(border=1)
    qr.add_data(addr); qr.make(fit=True)
    console.print(Panel.fit(f"[green]Address:[/green]\n[cyan]{addr}[/cyan]", title="QR Info"))
    console.print("Scan this QR for receiving DOGE:\n")
    qr.print_ascii(invert=True)


def get_doge_price_usdt():
    try:
        res = requests.get("https://api.coinbase.com/v2/prices/DOGE-USDT/spot")
        return float(res.json()['data']['amount'])
    except:
        return None


def send_doge():
    if not wallet_exists():
        console.print("[red]❌ No wallet found.[/red]\n"); return
    w = Wallet(WALLET_NAME, db_uri=f"sqlite:///{DB_PATH}")
    to_addr = Prompt.ask("Enter recipient DOGE address")
    amount = float(Prompt.ask("Enter amount in DOGE"))
    fee_usdt = float(Prompt.ask("Desired fee in USDT"))
    price = get_doge_price_usdt()
    if price is None:
        console.print("[red]❌ Could not fetch DOGE price.[/red]\n"); return
    fee_doge = fee_usdt / price
    fee_sats = int(fee_doge * 1e8)

    try:
        tx = w.send_to(to_addr, amount, fee=fee_sats, offline=False, replace_by_fee=True)
        console.print(Panel.fit(f"[green]✅ Sent![/green]\n[cyan]TXID:[/cyan] {tx.txid}"))
        console.print()
    except Exception as e:
        console.print(f"[red]❌ Error sending DOGE: {e}[/red]\n")


def main_menu():
    while True:
        console.print(Panel("[bold yellow]DOGE Wallet CLI[/bold yellow]",
                            subtitle="🔐 Secure • Local • Simple", expand=False))
        if wallet_exists(): console.print("1. View Wallet")
        else: console.print("1. Create Wallet")
        console.print("2. Receive DOGE\n3. Send DOGE\n4. Exit")
        choice = Prompt.ask("Select", choices=["1", "2", "3", "4"])
        if choice == "1":
            view_wallet() if wallet_exists() else create_wallet()
        elif choice == "2":
            receive_doge()
        elif choice == "3":
            send_doge()
        else:
            console.print("[bold red]Goodbye![/bold red]"); break


if __name__ == "__main__":
    main_menu()
