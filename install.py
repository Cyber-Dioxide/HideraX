import os
import sys
import platform
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

# Define all common packages
REQUIREMENTS = [
    "rich>=13.5.2",
    "web3>=6.12.0",
    "tronpy>=0.4.0",
    "eth-account>=0.9.0",
    "requests>=2.31.0",
    "bitcoinlib>=0.6.14",
    "rgbprint~=4.0.2",
    "qrcode~=8.2",
    "base58~=2.1.1",
    "pycoin~=0.92.20241201",
    "pynacl"
]

MONERO_PKG = "monero"

def install_package(package, allow_broken=False):
    try:
        args = [sys.executable, "-m", "pip", "install", package]
        if allow_broken:
            args += ["--break-system-packages"]
        subprocess.check_call(args)
        console.print(f"[green]✔ Installed:[/green] [bold]{package}[/bold]")
    except subprocess.CalledProcessError as e:
        if not allow_broken:
            console.print(f"[yellow]⚠ Retrying with --break-system-packages for:[/yellow] [bold]{package}[/bold]")
            install_package(package, allow_broken=True)
        else:
            console.print(f"[red]✘ Failed to install:[/red] [bold]{package}[/bold]")
            console.print(f"[dim]Error: {e}[/dim]")

def main():
    console.print(Panel.fit("🚀 [bold cyan]Starting Dependency Installation[/bold cyan]"))

    for pkg in REQUIREMENTS:
        install_package(pkg)

    if platform.system().lower() == "linux":
        console.print("\n[bold magenta]🔧 Linux detected! Attempting to install monero...[/bold magenta]")
        install_package(MONERO_PKG)
    else:
        console.print(Panel.fit(
            "❌ Skipping 'monero' installation.\n[bold yellow]This library is Linux-only.[/bold yellow]",
            title="⚠️ Notice", border_style="red", padding=(1, 2)
        ))

    console.print(Panel.fit(
        "[bold green]🎉 All done! You're ready to run the wallet CLI suite.[/bold green]",
        title="✅ Success", border_style="green"))


if __name__ == "__main__":
    main()
