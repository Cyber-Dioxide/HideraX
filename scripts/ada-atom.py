#!/usr/bin/env python3
"""
Fixed Multi Cold Wallet CLI — ADA / ATOM (receive-only)
- Generates a 24-word BIP39 mnemonic (string)
- Derives first 3 addresses for ADA, ATOM
- Tries to produce native addresses (Cardano Shelley, Cosmos)
- Robust across different versions of bip_utils
- Saves wallet_info.json (WARNING: contains sensitive data)
"""
from typing import List, Dict, Any
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes, Bip39MnemonicGenerator, Bip39WordsNum, Bip39MnemonicValidator, Bip32Slip10Ed25519
import os
import json
import shutil
import binascii
import qrcode

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

# Paths
WALLET_DIR = "wallet_Staking"
INFO_PATH = os.path.join(WALLET_DIR, "wallet_info.json")
BACKUP_PATH = os.path.join(WALLET_DIR, "wallet_info_corrupt_backup.json")

console = Console()


# ---------- Helpers ----------
def ensure_dir():
    os.makedirs(WALLET_DIR, exist_ok=True)


def wallet_exists() -> bool:
    return os.path.exists(INFO_PATH)


def safe_load_json(path: str) -> Dict[str, Any]:
    """Safely load wallet JSON file."""
    if not os.path.exists(path):
        return {}
    try:
        if os.path.getsize(path) == 0:
            return {}
    except Exception:
        pass

    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as je:
        console.print(Panel.fit(f"[yellow]⚠️ Wallet file corrupted. Backing up and resetting.[/yellow]\n{je}",
                                title="Wallet Load Warning", border_style="yellow"))
        try:
            ensure_dir()
            shutil.copy2(path, BACKUP_PATH)
            console.print(f"[yellow]Backed up corrupt file to {BACKUP_PATH}[/yellow]")
        except Exception:
            console.print("[red]Failed to backup corrupt wallet file.[/red]")
        return {}
    except Exception as e:
        console.print(Panel.fit(f"[red]Error reading wallet file: {e}[/red]",
                                title="Read Error", border_style="red"))
        return {}


def save_wallet_info(data: Dict[str, Any]):
    ensure_dir()
    with open(INFO_PATH, "w") as f:
        json.dump(data, f, indent=4)


def to_str_mnemonic(mobj) -> str:
    if isinstance(mobj, str):
        return mobj
    try:
        return mobj.ToStr()
    except Exception:
        return str(mobj)


def is_valid_mnemonic(mnemonic: str) -> bool:
    """Validate mnemonic across possible bip_utils versions."""
    if not isinstance(mnemonic, str):
        mnemonic = to_str_mnemonic(mnemonic)
    try:
        v = Bip39MnemonicValidator()
        return v.IsValid(mnemonic)
    except Exception:
        try:
            Bip39SeedGenerator(mnemonic).Generate()
            return True
        except Exception:
            return False


def pubkey_to_hex(pub) -> str:
    try:
        return pub.ToHex()
    except:
        return binascii.hexlify(pub.RawCompressed().ToBytes()).decode()


def privkey_to_hex(priv) -> str:
    try:
        return priv.ToHex()
    except:
        return binascii.hexlify(priv.Raw().ToBytes()).decode()


# ---------- Derivation ----------
def derive_ada_addresses(seed_bytes: bytes, count: int = 3) -> List[Dict[str, Any]]:
    """Derive Cardano Shelley (or fallback) addresses."""
    out = []
    try:
        if hasattr(Bip44Coins, "CARDANO_SHELLEY"):
            bip44_ada = Bip44.FromSeed(seed_bytes, Bip44Coins.CARDANO_SHELLEY)
            for i in range(count):
                ctx = bip44_ada.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(i)
                pub, priv = ctx.PublicKey(), ctx.PrivateKey()
                try:
                    addr = pub.ToAddress()
                except Exception:
                    addr = pubkey_to_hex(pub)
                out.append({
                    "index": i,
                    "address": addr,
                    "pub": pubkey_to_hex(pub),
                    "priv": privkey_to_hex(priv),
                    "method": "bip44_cardano_shelley"
                })
            return out
        else:
            raise AttributeError("CARDANO_SHELLEY not in Bip44Coins")
    except Exception as e:
        console.print(Panel.fit(f"[yellow]⚠️ ADA Bip44 derivation failed: {e}[/yellow]",
                                title="ADA Fallback", border_style="yellow"))

    # Fallback CIP-1852 path
    for i in range(count):
        try:
            ctx = Bip32Slip10Ed25519.FromSeed(seed_bytes).DerivePath(f"m/1852'/1815'/0'/0/{i}")
            pub, priv = ctx.PublicKey(), ctx.PrivateKey()
            out.append({
                "index": i,
                "address": pubkey_to_hex(pub),
                "pub": pubkey_to_hex(pub),
                "priv": privkey_to_hex(priv),
                "method": "ed25519_fallback"
            })
        except Exception as e:
            out.append({"index": i, "error": str(e)})
    return out


def derive_atom_addresses(seed_bytes: bytes, count: int = 3) -> List[Dict[str, Any]]:
    """Derive Cosmos (ATOM) addresses."""
    out = []
    try:
        if hasattr(Bip44Coins, "COSMOS"):
            bip_atom = Bip44.FromSeed(seed_bytes, Bip44Coins.COSMOS)
            for i in range(count):
                ctx = bip_atom.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(i)
                pub, priv = ctx.PublicKey(), ctx.PrivateKey()
                try:
                    addr = pub.ToAddress()
                except Exception:
                    addr = pubkey_to_hex(pub)
                out.append({
                    "index": i,
                    "address": addr,
                    "pub": pubkey_to_hex(pub),
                    "priv": privkey_to_hex(priv),
                    "method": "bip44_cosmos"
                })
            return out
        else:
            raise AttributeError("COSMOS not in Bip44Coins")
    except Exception as e:
        for i in range(count):
            out.append({"index": i, "error": f"Cosmos derive failed: {e}"})
    return out


# ---------- Core actions ----------
def create_wallet():
    ensure_dir()
    mobj = Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_24)
    mnemonic = to_str_mnemonic(mobj)

    if not is_valid_mnemonic(mnemonic):
        console.print("[red]❌ Generated mnemonic failed validation. Abort.[/red]")
        return

    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()

    ada_addrs = derive_ada_addresses(seed_bytes, count=3)
    atom_addrs = derive_atom_addresses(seed_bytes, count=3)

    wallet_info = {
        "mnemonic": mnemonic,
        "mnemonic_type": "BIP39",
        "chains": {"ADA": ada_addrs, "ATOM": atom_addrs}
    }
    save_wallet_info(wallet_info)

    console.print(Panel.fit(f"[bold yellow]Write this down and store offline[/bold yellow]\n\n{mnemonic}",
                            title="🧠 24-Word Mnemonic", border_style="green"))

    # Preview table
    t = Table(title="Derived Addresses (index 0)", header_style="bold magenta")
    t.add_column("Chain", style="cyan")
    t.add_column("Index", style="yellow")
    t.add_column("Address / Note", style="green", overflow="fold")
    t.add_row("ADA", "0", ada_addrs[0].get("address", "error"))
    t.add_row("ATOM", "0", atom_addrs[0].get("address", "error"))
    console.print(Panel.fit(t, title="📬 Receive Addresses", border_style="blue"))

    console.print(Panel.fit(
        "[yellow]⚠️ SECURITY: wallet_info.json contains mnemonic and private keys. Keep it air-gapped and encrypted.[/yellow]\n"
        "• ADA: attempts CARDANO_SHELLEY (CIP-1852), fallback ed25519.\n"
        "• ATOM: standard BIP44 (m/44'/118'/0'/0/x).",
        title="Compatibility Note", border_style="yellow"
    ))


def view_wallet():
    info = safe_load_json(INFO_PATH)
    if not info:
        console.print("[red]❌ Wallet not found or empty. Create it first.[/red]")
        return

    tbl = Table(title="Derived Addresses (first 3)", header_style="bold magenta")
    tbl.add_column("Chain", style="cyan")
    tbl.add_column("Index", style="yellow")
    tbl.add_column("Address / Note", style="green", overflow="fold")

    for chain in ("ADA", "ATOM"):
        for entry in info.get("chains", {}).get(chain, []):
            idx = entry.get("index", "-")
            addr = entry.get("address") or entry.get("error") or "n/a"
            tbl.add_row(chain, str(idx), addr)

    console.print(Panel.fit(tbl, title="Stored Derived Addresses", border_style="blue"))

    # Show mnemonic (if exists)
    mnemonic = info.get("mnemonic")
    if mnemonic:
        console.print(Panel.fit(
            f"[bold yellow]Write this down and store offline[/bold yellow]\n\n{mnemonic}",
            title="🧠 24-Word Mnemonic",
            border_style="green"
        ))

    console.print(Panel.fit(
        "Recoverable in Yoroi/Daedalus (ADA) and Keplr/Leap (ATOM). "
        "⚠️ Not importable in MetaMask (EVM-only).",
        title="Recovery"
    ))

    


def receive_cli():
    info = safe_load_json(INFO_PATH)
    if not info:
        console.print("[red]❌ Wallet not found. Create it first.[/red]")
        return

    chain = Prompt.ask("Choose chain", choices=["ADA", "ATOM"], default="ADA")
    entries = info.get("chains", {}).get(chain, [])
    if not entries:
        console.print("[red]No derived addresses for this chain.[/red]")
        return

    table = Table(title=f"📥 Receive {chain}", header_style="bold magenta")
    table.add_column("Index", style="cyan")
    table.add_column("Address", style="green", overflow="fold")
    for e in entries:
        table.add_row(str(e.get("index", "?")), e.get("address", "n/a"))
    console.print(table)

    choice = Prompt.ask("Enter index to show QR", choices=[str(i) for i in range(len(entries))], default="0")
    addr = entries[int(choice)].get("address", "")
    console.print(Panel.fit(f"[bold cyan]{chain} Address:[/bold cyan]\n{addr}", title="Selected Address"))

    qr = qrcode.QRCode(border=1)
    qr.add_data(addr)
    qr.make(fit=True)
    console.print("[bold light_green]Scan this QR to receive funds:[/bold light_green]\n")
    qr.print_ascii(invert=True)


def main_menu():
    while True:
        console.print(Panel("[bold yellow]Multi Cold Wallet CLI — ADA / ATOM[/bold yellow]",
                            subtitle="🔐 Secure • BIP39 Seed • Receive-only", expand=False))
        console.print("[bold blue]1.[/bold blue] Create Wallet" if not wallet_exists() else "[bold blue]1.[/bold blue] View Wallet")
        console.print("[bold blue]2.[/bold blue] Receive (Show address + QR)")
        console.print("[bold blue]3.[/bold blue] Exit")
        choice = Prompt.ask("\n[bold green]Select an option[/bold green]", choices=["1", "2", "3"])

        if choice == "1":
            if wallet_exists():
                view_wallet()
            else:
                create_wallet()
        elif choice == "2":
            receive_cli()
        elif choice == "3":
            console.print("[bold red]Goodbye![/bold red]")
            break


if __name__ == "__main__":
    main_menu()
