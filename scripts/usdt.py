import os
import json
import sys

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from web3 import Web3
from tronpy import Tron
from tronpy.keys import PrivateKey

console = Console()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WALLET_DIR = os.path.join(BASE_DIR, "wallet_USDT")
WALLET_FILE = os.path.join(WALLET_DIR, "wallet_info.json")


# Infura or Alchemy or your Ethereum node
ETH_RPC_URL = "https://mainnet.infura.io/v3/ae6132a817bc4f029109a313dd848182"
w3 = Web3(Web3.HTTPProvider(ETH_RPC_URL))

# Tron client (mainnet)
tron = Tron()

# USDT contract addresses
USDT_ERC20_CONTRACT = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
USDT_TRC20_CONTRACT = "TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj"  # TRC20 USDT contract address

def wallet_exists():
    return os.path.exists(WALLET_FILE)


def view_wallet():
    wallet = load_wallet()
    if not wallet:
        print("Wallet not found.")
        return

    eth_address = wallet['ethereum']['address']
    eth_pk = wallet['ethereum']['private_key']
    tron_address = wallet['tron']['address']
    tron_pk = wallet['tron']['private_key']

    console.print(Panel.fit(f"[bold cyan]Ethereum Wallet[/bold cyan]\n"
                            f"Address: {eth_address}\n"
                            f"Private Key: {eth_pk}\n\n"
                            f"[bold magenta]Tron Wallet[/bold magenta]\n"
                            f"Address: {tron_address}\n"
                            f"Private Key: {tron_pk}"))

def send_usdt():
    wallet = load_wallet()
    if not wallet:
        return

    console.print(Panel.fit("[bold cyan]Select Network[/bold cyan]\n[1] Ethereum (ERC20)\n[2] Tron (TRC20)"))
    network_choice = Prompt.ask("Enter your choice", choices=["1", "2"], default="1")

    to_address = Prompt.ask("Enter recipient address")
    amount_str = Prompt.ask("Enter amount in USDT")

    try:
        amount = float(amount_str)
    except ValueError:
        console.print("[red]Invalid amount entered.[/red]")
        return

    if network_choice == "1":
        gas_price_gwei = Prompt.ask("Enter gas price in Gwei (recommended: 15-40)", default="20")
        try:
            gas_price_gwei = float(gas_price_gwei)
        except ValueError:
            console.print("[red]Invalid gas price.[/red]")
            return

        try:
            send_eth_usdt(wallet, to_address, amount, gas_price_gwei)
        except Exception as e:
            console.print(f"[red]Failed to send ERC20 USDT: {e}[/red]")

    elif network_choice == "2":
        try:
            send_trc20_usdt(wallet, to_address, amount)
        except Exception as e:
            console.print(f"[red]Failed to send TRC20 USDT: {e}[/red]")


def create_wallet():
    if os.path.exists(WALLET_FILE):
        console.print("[yellow]Wallet already exists.[/yellow]")
        return

    os.makedirs(WALLET_DIR, exist_ok=True)

    # Ethereum Wallet
    eth_account = w3.eth.account.create()
    eth_address = eth_account.address
    eth_private_key = eth_account.key.hex()

    # Tron Wallet
    tron_priv_key = PrivateKey.random()
    tron_address = tron_priv_key.public_key.to_base58check_address()
    tron_priv_key_hex = tron_priv_key.hex()

    wallet_info = {
        "ethereum": {
            "address": eth_address,
            "private_key": eth_private_key
        },
        "tron": {
            "address": tron_address,
            "private_key": tron_priv_key_hex
        }
    }

    with open(WALLET_FILE, "w") as f:
        json.dump(wallet_info, f, indent=4)

    console.print(Panel.fit(f"[green]Wallet created![/green]\n\n"
                            f"[bold cyan]Ethereum Address:[/bold cyan] {eth_address}\n"
                            f"[bold cyan]Tron Address:[/bold cyan] {tron_address}",
                            title="USDT Wallet Info"))


def load_wallet():
    if not os.path.exists(WALLET_FILE):
        console.print("[red]No wallet found. Please create one first.[/red]")
        return None
    with open(WALLET_FILE) as f:
        return json.load(f)


def send_trc20_usdt(wallet, to_address, amount):
    from tronpy import Tron
    from tronpy.keys import PrivateKey

    private_key = wallet['tron']['private_key']
    from_address = wallet['tron']['address']

    tron = Tron()
    client_key = PrivateKey(bytes.fromhex(private_key))
    contract = tron.get_contract(USDT_TRC20_CONTRACT)

    try:
        amount_in_wei = int(float(amount) * 1e6)  # 6 decimals
        txn = (
            contract.functions.transfer(to_address, amount_in_wei)
            .with_owner(from_address)
            .fee_limit(1_000_000)
            .build()
            .sign(client_key)
        )
        result = txn.broadcast()
        if result['result']:
            console.print(f"[green]TRC20 USDT sent! Transaction ID: {txn.txid}[/green]")
        else:
            console.print("[red]Failed to send TRC20 USDT.[/red]")
    except Exception as e:
        console.print(f"[red]Error sending TRC20 USDT: {e}[/red]")


def send_eth_usdt(wallet, to_address, amount, gas_price_gwei):
    from web3 import Web3

    erc20_abi = [
        {
            "constant": False,
            "inputs": [
                {"name": "_to", "type": "address"},
                {"name": "_value", "type": "uint256"}
            ],
            "name": "transfer",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function",
        }
    ]

    private_key = wallet['ethereum']['private_key']
    from_address = wallet['ethereum']['address']

    contract = w3.eth.contract(address=USDT_ERC20_CONTRACT, abi=erc20_abi)

    try:
        nonce = w3.eth.get_transaction_count(from_address)
        gas_price = w3.to_wei(gas_price_gwei, 'gwei')
        amount_in_wei = int(float(amount) * 1e6)

        tx = contract.functions.transfer(to_address, amount_in_wei).buildTransaction({
            'chainId': 1,
            'gas': 100000,
            'gasPrice': gas_price,
            'nonce': nonce,
        })

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        console.print(f"[green]ERC20 USDT sent! TxHash: {tx_hash.hex()}[/green]")
    except Exception as e:
        console.print(f"[red]Error sending ERC20 USDT: {e}[/red]")


def get_trc20_usdt_balance(address):
    contract = tron.get_contract(USDT_TRC20_CONTRACT)
    balance = contract.functions.balanceOf(address)
    return balance / 1e6


def receive_usdt():
    wallet = load_wallet()
    if not wallet:
        print("Wallet not found.")
        return
    eth_addr = wallet['ethereum']['address']
    tron_addr = wallet['tron']['address']

    console.print(Panel.fit(f"[bold green]Your USDT Receiving Addresses[/bold green]\n\n"
                            f"[bold cyan]Ethereum (ERC20):[/bold cyan] {eth_addr}\n"
                            f"[bold magenta]Tron (TRC20):[/bold magenta] {tron_addr}"))


def print_menu(existing_wallet):
    console.print(Panel.fit(
        "[bold white]╭────────────────────────╮\n"
        "│       [cyan]USDT Wallet CLI[/cyan]       │\n"
        "╰─ [magenta]ERC20[/magenta] + [green]TRC20[/green] Support ─╯",
        border_style="bright_blue"))

    if existing_wallet:
        console.print("[bold green][1][/bold green] View Wallet")
        console.print("[bold green][2][/bold green] Receive USDT")
        console.print("[bold green][3][/bold green] Send USDT")
        console.print("[bold red][4][/bold red] Exit")
    else:
        console.print("[bold green][1][/bold green] Create Wallet")
        console.print("[bold red][4][/bold red] Exit")

console.print(Panel.fit(
    "[bold cyan]Welcome to the USDT Wallet CLI[/bold cyan]\n[dim]Secure | Simple | Multi-chain[/dim]",
    border_style="white", title="USDT CLI", title_align="left"))
def main_menu():
    if wallet_exists():
        while True:
            print_menu(existing_wallet=True)

            choice = Prompt.ask("[bold yellow]Select an option[/bold yellow]", choices=["1", "2", "3", "4"])
            if choice == '1':
                view_wallet()
            elif choice == '2':
                receive_usdt()
            elif choice == '3':
                send_usdt()
            elif choice == '4':
                console.print("[bold red]Exiting...[/bold red]")
                sys.exit()
    else:
        while True:
            print_menu(existing_wallet=False)
            choice = Prompt.ask("[bold yellow]Select an option[/bold yellow]", choices=["1", "4"])
            if choice == '1':
                create_wallet()
            elif choice == '4':
                console.print("[bold red]Exiting...[/bold red]")
                sys.exit()


if __name__ == "__main__":
    main_menu()
