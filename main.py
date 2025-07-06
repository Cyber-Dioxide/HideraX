import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from rgbprint import gradient_print
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.style import Style
from rich.table import Table
from rich import box
from rich.text import Text

console = Console()

# Get the absolute path to the directory this script resides in
BASE_DIR = Path(__file__).parent.resolve()
SCRIPTS_DIR = BASE_DIR / "scripts"

logo = """

 __    __   __   _______   _______ .______          ___      ___   ___ 
|  |  |  | |  | |       \ |   ____||   _  \        /   \     \  \ /  / 
|  |__|  | |  | |  .--.  ||  |__   |  |_)  |      /  ^  \     \  V  /  
|   __   | |  | |  |  |  ||   __|  |      /      /  /_\  \     >   <   
|  |  |  | |  | |  '--'  ||  |____ |  |\  \----./  _____  \   /  .  \  
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

    # Center each line manually
    centered_logo = "\n".join(line.center(term_width) for line in lines)

    # Print gradient centered logo
    gradient_print(centered_logo, start_color="#8e44ad", end_color="#1abc9c")


def print_menu():
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

    table.add_row("1", "USDT Wallet", "[TRC20] | [ERC20]")
    table.add_row("2", "BTC Wallet", "Bitcoin Network")
    table.add_row("3", "ETH Wallet", "Ethereum Network")
    table.add_row("4", "POL Wallet", "Polygon Network")
    table.add_row("5", "LTC Wallet", "Litecoin Network")
    table.add_row("6", "DOGE Wallet", "Dogecoin Network")
    table.add_row("0", "[bold red]Exit[/bold red]", "Leave application")

    console.print(table)


def main():
    while True:
        clear_console()
        print_menu()

        choice = Prompt.ask("[bold green]Enter your choice[/bold green]", choices=["0", "1", "2", "3", "4", "5", "6"],
                            default="0")

        script_map = {
            "1": "usdt.py",
            "2": "btc.py",
            "3": "eth.py",
            "4": "pol.py",
            "5": "ltc.py",
            "6": "doge.py"
        }

        if choice == "0":
            console.print("\n[bold green]✓ Exiting wallet manager. Have a great day![/bold green]\n")
            sys.exit(0)
        elif choice in script_map:
            execute_script(script_map[choice])
        else:
            console.print("[bold red]✖ Invalid option selected.[/bold red]")

        console.print("\n[dim]Press Enter to return to the main menu...[/dim]")
        input()


if __name__ == "__main__":
    main()
