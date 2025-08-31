import os
import platform
import shutil
import sys
from pathlib import Path

from rgbprint import gradient_print
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich import box

console = Console()

# Get the absolute path to the directory this script resides in
BASE_DIR = Path(__file__).parent.resolve()
SCRIPTS_DIR = BASE_DIR / "scripts"

logo = """

 __    __   __   _______   _______ .______          ___      ___   ___ 
|  |  |  | |  | |       \ |   ____||   _  \        /   \     \  \ /  / 
|  |__|  | |  | |  .--.  ||  |__   |  |_)  |      /  ^  \     \  V  /  
|   __   | |  | |  |  |  ||   __|  |      /      /  /_\  \     >   <   
|  |  |  | |  | |  '--'  ||  |____ |  | \  \----./  _____  \   /  .  \  
|__|  |__| |__| |_______/ |_______|| _| `._____/__/     \__\ /__/ \__\ 
                                                                                                       
"""


def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


def execute_script(script_name):
    script_path = SCRIPTS_DIR / script_name
    full_path = str(script_path.resolve())

    if not script_path.exists():
        console.print(f"[bold red]✖ File not found:[/bold red] {full_path}")
        return

    try:
        command = f'py -3 "{full_path}"' if platform.system() == "Windows" else f'python3 "{full_path}"'
        os.system(command)
    except Exception as e:
        console.print(f"[bold red]✖ Execution failed:[/bold red] {e}")


def print_banner():
    term_width = shutil.get_terminal_size().columns
    lines = logo.strip("\n").splitlines()
    centered_logo = "\n".join(line.center(term_width) for line in lines)
    gradient_print(centered_logo, start_color="#8e44ad", end_color="#1abc9c")


def print_menu(script_map):
    clear_console()
    print()
    print_banner()
    console.print("[bold white]Powered by [bold magenta]Hiderox Technologies[/bold magenta][/bold white]",
                  justify="center")
    console.print("[bold blue underline]www.hiderox.com[/bold blue underline]\n", justify="center")
    console.print(Panel.fit(
        "[bold cyan]🚀 Multi-Crypto Wallet Manager[/bold cyan]",
        subtitle="Secure • Flexible • Fast",
        style="bold blue",
        padding=(1, 4)
    ))

    table = Table(title="Select Wallet Option", box=box.SIMPLE, title_style="bold magenta")
    table.add_column("Option", justify="center", style="bold yellow")
    table.add_column("Wallet", style="bold white")
    table.add_column("Network Info", style="dim")

    for key, info in sorted(script_map.items(), key=lambda x: x[1]["name"].lower()):
        table.add_row(key, info["name"], info["network"])

    table.add_row("0", "[bold red]Exit[/bold red]", "Leave application")
    console.print(table)


def main():
    # Unified wallet mapping
    script_map = {
        "1": {"name": "ADA Wallet", "network": "Cardano [Receive-Only]", "script": "ada-atom.py"},
        "2": {"name": "ATOM Wallet", "network": "Cosmos [Receive-Only]", "script": "ada-atom.py"},
        "3": {"name": "BCH Wallet", "network": "Bitcoin Cash Network", "script": "bch.py"},
        "4": {"name": "BNB Wallet", "network": "Binance Smart Chain", "script": "bnb.py"},
        "5": {"name": "BTC Wallet", "network": "Bitcoin Network", "script": "btc.py"},
        "6": {"name": "DASH Wallet", "network": "Dash [Receive-Only]", "script": "dash.py"},
        "7": {"name": "DOGE Wallet", "network": "Dogecoin Network", "script": "doge.py"},
        "8": {"name": "ETH Wallet", "network": "Ethereum Network", "script": "eth.py"},
        "9": {"name": "LTC Wallet", "network": "Litecoin Network", "script": "ltc.py"},
        "10": {"name": "POL Wallet", "network": "Polygon Network", "script": "pol.py"},
        "11": {"name": "SOL Wallet", "network": "Solana [Receive-Only]", "script": "sol.py"},
        "12": {"name": "USDT Wallet", "network": "[TRC20] | [ERC20]", "script": "usdt.py"},
        "13": {"name": "XMR Wallet", "network": "Monero [Receive-Only • Linux]", "script": "xmr.py"},
        "14": {"name": "ZEC Wallet", "network": "Zcash [Receive-Only]", "script": "zec.py"},
    }

    while True:
        clear_console()
        print_menu(script_map)

        choice = Prompt.ask(
            "[bold green]Enter your choice[/bold green]",
            choices=[str(i) for i in range(0, len(script_map) + 1)],
            default="0"
        )

        if choice == "0":
            console.print("\n[bold green]✓ Exiting wallet manager. Have a great day![/bold green]\n")
            sys.exit(0)
        elif choice in script_map:
            # XMR restriction
            if script_map[choice]["name"].startswith("XMR") and platform.system() != "Linux":
                console.print("[bold red]✖ XMR support is currently available for Linux only.[/bold red]")
            else:
                execute_script(script_map[choice]["script"])
        else:
            console.print("[bold red]✖ Invalid option selected.[/bold red]")

        console.print("\n[dim]Press Enter to return to the main menu...[/dim]")
        input()


if __name__ == "__main__":
    main()
