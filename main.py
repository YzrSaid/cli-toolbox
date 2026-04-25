#!/usr/bin/env python3

from __future__ import annotations

import os
import sys
import webbrowser

from pyfiglet import figlet_format
from rich.console import Console
from rich.panel import Panel

from tools.image_converter.run import main as image_converter
from tools.yt_downloader.run import main as yt_downloader

PROJECT_NAME = "CLI Toolbox"
DEVELOPER = "Mohammad Aldrin Said"
SOURCE_CODE_URL = "https://github.com/YzrSaid/cli-toolbox"
VERSION = "1.0"

console = Console()


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def show_banner() -> None:
    banner = figlet_format(PROJECT_NAME, font="big")
    console.print(f"[bold bright_green]{banner}[/bold bright_green]")
    info = (
        f"[cyan][>][/cyan] Github  : [green]{SOURCE_CODE_URL}[/green]\n"
        f"[cyan][>][/cyan] Author  : [green]{DEVELOPER}[/green]\n"
        f"[cyan][>][/cyan] Version : [green]{VERSION}[/green]"
    )
    console.print(Panel(info, border_style="bright_black"))


def show_menu() -> None:
    menu = (
        "[bold green][1][/bold green] Image Converter\n"
        "[bold green][2][/bold green] YouTube Downloader\n"
        "[bold green][3][/bold green] View Source Code\n\n"
        "[bold red][4][/bold red] Exit"
    )
    console.print(
        Panel(
            menu, title="[bold yellow]Main Menu[/bold yellow]", border_style="white")
    )


def open_source_code() -> None:
    console.print(
        f"\n[bold cyan]Opening:[/bold cyan] [green]{SOURCE_CODE_URL}[/green]")
    try:
        opened = webbrowser.open(SOURCE_CODE_URL)
        if not opened:
            console.print("[red]Unable to open browser automatically.[/red]")
            console.print(f"Source Code: [green]{SOURCE_CODE_URL}[/green]")
    except Exception:
        console.print("[red]Unable to open browser automatically.[/red]")
        console.print(f"Source Code: [green]{SOURCE_CODE_URL}[/green]")


def main() -> None:
    while True:
        clear_screen()
        show_banner()
        show_menu()

        choice = input("\n[>] Select Option: ").strip()

        if choice == "1":
            clear_screen()
            image_converter()

        elif choice == "2":
            clear_screen()
            yt_downloader()

        elif choice == "3":
            open_source_code()
            input("\nPress Enter to return to menu...")

        elif choice == "4":
            console.print("\n[bold red]Exiting...[/bold red]")
            sys.exit()

        else:
            console.print("[red]Invalid option.[/red]")
            input("Press Enter to continue...")


if __name__ == "__main__":
    main()
