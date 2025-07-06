import os
import platform
import shutil
import sys
from pathlib import Path
from pynput import keyboard

from rgbprint import gradient_print
from rich.console import Console
from rich.panel import Panel
from rich import box
from rich.table import Table
from rich.live import Live

console = Console()
BASE_DIR = Path(__file__).parent.resolve()
SCRIPTS_DIR = BASE_DIR / "scripts"

logo = """
Hiderax
"""

wallet_options = [
    ("1", "USDT Wallet", "[TRC20] | [ERC20]"),
    ("2", "BTC Wallet", "Bitcoin Network"),
    ("3", "ETH Wallet", "Ethereum Network"),
    ("4", "POL Wallet", "Polygon Network"),
    ("5", "LTC Wallet", "Litecoin Network"),
    ("6", "DOGE Wallet", "Dogecoin Network"),
    ("7", "XMR Wallet", "[Linux Only] Monero Network"),
    ("8", "ZEC Wallet", "Zcash Network"),
    ("9", "DASH Wallet", "Dash Network"),
    ("10", "BNB Wallet", "Binance Chain (BEP20)"),
    ("0", "[bold red]Exit[/bold red]", "Leave application")
]

selected_index = 0
exit_flag = False
enter_pressed = False


def clear_console():
    pass


def execute_script(script_name):
    path = SCRIPTS_DIR / script_name
    if not path.exists():
        console.print(f"[red]✖ Script not found:[/red] {script_name}")
        return
    command = f'py -3 "{path}"' if platform.system() == "Windows" else f'python3 "{path}"'
    os.system(command)


def print_banner():
    term_width = shutil.get_terminal_size().columns
    lines = logo.strip("\n").splitlines()
    centered_logo = "\n".join(line.center(term_width) for line in lines)
    gradient_print(centered_logo, start_color="#8e44ad", end_color="#1abc9c")


def render_wallet_menu():
    table = Table(title="Select Wallet Option (↑ ↓ Enter)", box=box.SIMPLE, title_style="bold magenta")
    table.add_column("Option", justify="center", style="bold yellow")
    table.add_column("Wallet", style="bold white")
    table.add_column("Network Info", style="dim")

    for i, (opt, wallet, net) in enumerate(wallet_options):
        row_style = "on blue" if i == selected_index else ""
        table.add_row(opt, wallet, net, style=row_style)

    return table


def on_press(key):
    global selected_index, exit_flag, enter_pressed

    if key == keyboard.Key.down:
        if selected_index < len(wallet_options) - 1:
            selected_index += 1

    elif key == keyboard.Key.up:
        if selected_index > 0:
            selected_index -= 1

    elif key == keyboard.Key.enter:
        enter_pressed = True
        exit_flag = True
        return False

    elif key == keyboard.Key.esc:
        exit_flag = True
        return False


def wallet_launcher():
    global exit_flag, selected_index, enter_pressed

    while True:

        exit_flag = False
        enter_pressed = False

        print_banner()
        console.print("[bold white]Powered by [bold magenta]Hiderox Technologies[/bold magenta][/bold white]", justify="center")
        console.print("[bold blue underline]www.hiderox.com[/bold blue underline]\n", justify="center")
        console.print(Panel.fit("[bold cyan]🚀 Multi-Crypto Wallet Manager[/bold cyan]",
                                subtitle="Secure • Flexible • Fast", style="bold blue", padding=(1, 4)))

        listener = keyboard.Listener(on_press=on_press)
        listener.start()

        with Live(render_wallet_menu(), refresh_per_second=10, screen=True) as live:
            while not exit_flag:
                live.update(render_wallet_menu())

        listener.stop()

        selected_choice = wallet_options[selected_index][0]
        script_map = {
            "1": "usdt.py",
            "2": "btc.py",
            "3": "eth.py",
            "4": "pol.py",
            "5": "ltc.py",
            "6": "doge.py",
            "7": "xmr.py",
            "8": "zec.py",
            "9": "dash.py",
            "10": "bnb.py"
        }

        if selected_choice == "0":
            console.print("\n[bold green]✓ Exiting wallet manager. Have a great day![/bold green]\n")
            sys.exit(0)

        if selected_choice in script_map:
            execute_script(script_map[selected_choice])

        console.print("\n[dim]Press Enter to return to the main menu...[/dim]")
        input()


if __name__ == "__main__":
    wallet_launcher()
