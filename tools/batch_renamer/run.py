#!/usr/bin/env python3
"""
Batch Renamer Tool

Rename files in a folder using structured naming patterns:
  1. Number only           → 001.jpg
  2. Prefix + Number       → photo_001.jpg
  3. Date + Number         → 2026-04-28_001.jpg
  4. Prefix + Date + Num   → photo_2026-04-28_001.jpg
  5. Date + Prefix + Num   → 2026-04-28_photo_001.jpg
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


class Cancelled(Exception):
    pass


class GoBack(Exception):
    pass


APP_NAME = "Batch Renamer"

DATE_FORMATS: dict[str, tuple[str, str]] = {
    "1": ("%Y-%m-%d", "YYYY-MM-DD  →  2026-04-28"),
    "2": ("%Y%m%d",   "YYYYMMDD    →  20260428"),
    "3": ("%d-%m-%Y", "DD-MM-YYYY  →  28-04-2026"),
    "4": ("%m-%d-%Y", "MM-DD-YYYY  →  04-28-2026"),
}

PATTERNS: dict[str, str] = {
    "1": "Number only            →  001.jpg",
    "2": "Prefix + Number        →  photo_001.jpg",
    "3": "Date + Number          →  2026-04-28_001.jpg",
    "4": "Prefix + Date + Number →  photo_2026-04-28_001.jpg",
    "5": "Date + Prefix + Number →  2026-04-28_photo_001.jpg",
}


# ─── Banner ───────────────────────────────────────────────────────────────────

def print_banner() -> None:
    console.print(
        Panel(
            f"[bold bright_green]{APP_NAME}[/bold bright_green]",
            border_style="green",
        )
    )


# ─── Prompts ──────────────────────────────────────────────────────────────────

def prompt_folder() -> Path:
    while True:
        console.print("[dim]Enter q to cancel.[/dim]")
        raw = input("Folder path: ").strip()
        if raw.lower() == "q":
            raise GoBack()
        if not raw:
            console.print("[red]Please enter a folder path.[/red]")
            continue
        path = Path(raw).expanduser().resolve()
        if not path.exists():
            console.print(f"[red]Folder does not exist:[/red] {path}")
            continue
        if not path.is_dir():
            console.print(f"[red]Path is not a folder:[/red] {path}")
            continue
        return path


def prompt_pattern() -> str:
    menu = "\n".join(
        f"[bold green][{k}][/bold green] {v}" for k, v in PATTERNS.items()
    ) + "\n\n[bold red][0][/bold red] Cancel"
    console.print(Panel(menu, title="[bold yellow]Naming Pattern[/bold yellow]", border_style="white"))
    while True:
        choice = input("\n[>] Select pattern (1-5): ").strip()
        if choice == "0":
            raise Cancelled()
        if choice in PATTERNS:
            return choice
        console.print("[red]Enter a number from 1 to 5.[/red]")


def prompt_prefix() -> str:
    console.print("[dim]Enter q to cancel.[/dim]")
    while True:
        prefix = input("Prefix: ").strip()
        if prefix.lower() == "q":
            raise GoBack()
        if prefix:
            return prefix
        console.print("[red]Please enter a prefix.[/red]")


def prompt_date_format() -> str:
    menu = "\n".join(
        f"[bold green][{k}][/bold green] {label}"
        for k, (_, label) in DATE_FORMATS.items()
    ) + "\n\n[bold red][0][/bold red] Cancel"
    console.print(Panel(menu, title="[bold yellow]Date Format[/bold yellow]", border_style="white"))
    while True:
        choice = input("\n[>] Select date format (1-4): ").strip()
        if choice == "0":
            raise Cancelled()
        if choice in DATE_FORMATS:
            return DATE_FORMATS[choice][0]
        console.print("[red]Enter a number from 1 to 4.[/red]")


def prompt_date_source() -> str:
    menu = (
        "[bold green][1][/bold green] Today's date"
        "  [dim](same date applied to all files)[/dim]\n"
        "[bold green][2][/bold green] File's modified date"
        "  [dim](each file gets its own date)[/dim]\n\n"
        "[bold red][0][/bold red] Cancel"
    )
    console.print(Panel(menu, title="[bold yellow]Date Source[/bold yellow]", border_style="white"))
    while True:
        choice = input("\n[>] Select date source (1-2): ").strip()
        if choice == "0":
            raise Cancelled()
        if choice == "1":
            return "today"
        if choice == "2":
            return "file"
        console.print("[red]Enter 1 or 2.[/red]")


def prompt_start_number() -> int:
    while True:
        raw = input("Start number [default: 1]: ").strip()
        if not raw:
            return 1
        try:
            n = int(raw)
            if n >= 0:
                return n
            console.print("[red]Must be 0 or greater.[/red]")
        except ValueError:
            console.print("[red]Enter a valid whole number.[/red]")


def prompt_padding() -> int:
    while True:
        raw = input("Digit padding [default: 3  →  001, 002, ...]: ").strip()
        if not raw:
            return 3
        try:
            n = int(raw)
            if n >= 1:
                return n
            console.print("[red]Must be at least 1.[/red]")
        except ValueError:
            console.print("[red]Enter a valid whole number.[/red]")


# ─── Name builder ─────────────────────────────────────────────────────────────

def resolve_date(file: Path, fmt: str, source: str, today_str: str) -> str:
    if source == "today":
        return today_str
    return datetime.fromtimestamp(file.stat().st_mtime).strftime(fmt)


def build_new_name(
    file: Path,
    pattern: str,
    number: int,
    padding: int,
    prefix: str,
    date_fmt: str,
    date_source: str,
    today_str: str,
) -> str:
    ext = file.suffix.lower()
    num = str(number).zfill(padding)

    if pattern == "1":
        stem = num
    elif pattern == "2":
        stem = f"{prefix}_{num}"
    elif pattern == "3":
        date = resolve_date(file, date_fmt, date_source, today_str)
        stem = f"{date}_{num}"
    elif pattern == "4":
        date = resolve_date(file, date_fmt, date_source, today_str)
        stem = f"{prefix}_{date}_{num}"
    else:  # 5
        date = resolve_date(file, date_fmt, date_source, today_str)
        stem = f"{date}_{prefix}_{num}"

    return stem + ext


# ─── Preview ──────────────────────────────────────────────────────────────────

def show_preview(files: list[Path], new_names: list[str]) -> None:
    table = Table(
        title="Rename Preview",
        border_style="bright_black",
        header_style="bold cyan",
        show_lines=False,
    )
    table.add_column("Original", style="dim", no_wrap=True)
    table.add_column("→", justify="center", style="bright_black", no_wrap=True)
    table.add_column("New Name", style="bold green", no_wrap=True)

    show_indices = list(range(min(5, len(files))))
    if len(files) > 6:
        for i in show_indices:
            table.add_row(files[i].name, "→", new_names[i])
        table.add_row("...", "", "...")
        table.add_row(files[-1].name, "→", new_names[-1])
    else:
        for i in range(len(files)):
            table.add_row(files[i].name, "→", new_names[i])

    console.print()
    console.print(table)
    console.print(f"\n[dim]Total: {len(files)} files[/dim]")


# ─── Post-action ─────────────────────────────────────────────────────────────

def prompt_post_action() -> str:
    menu = (
        "[bold green][1][/bold green] Rename another batch\n\n"
        "[bold red][2][/bold red] Back to main menu"
    )
    console.print(
        Panel(menu, title="[bold yellow]What's Next?[/bold yellow]", border_style="white")
    )
    while True:
        choice = input("\n[>] Select option: ").strip()
        if choice in {"1", "2"}:
            return choice
        console.print("[red]Enter 1 or 2.[/red]")


# ─── Rename executor ──────────────────────────────────────────────────────────

def do_rename(files: list[Path], new_names: list[str]) -> tuple[int, int]:
    success = 0
    failed = 0

    for file, new_name in zip(files, new_names):
        target = file.parent / new_name
        try:
            if target.exists() and target.resolve() != file.resolve():
                raise FileExistsError(f"Already exists: {new_name}")
            file.rename(target)
            console.print(
                f"  [bold green][OK][/bold green]   "
                f"{file.name} [dim]→[/dim] {new_name}"
            )
            success += 1
        except Exception as exc:
            console.print(
                f"  [bold red][FAIL][/bold red] "
                f"{file.name} [dim]→[/dim] {exc}"
            )
            failed += 1

    return success, failed


# ─── Entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    print_banner()

    while True:
        try:
            console.print("\n[bold cyan]Enter the folder containing the files to rename.[/bold cyan]")
            folder = prompt_folder()

            files = sorted(f for f in folder.iterdir() if f.is_file())
            if not files:
                console.print(f"\n[yellow]No files found in:[/yellow] {folder}")
                input("\nPress Enter to return...")
                return

            console.print(
                f"\n[cyan]Found[/cyan] [bold white]{len(files)}[/bold white] "
                f"[cyan]file(s) in[/cyan] [green]{folder}[/green]"
            )

            pattern = prompt_pattern()

            needs_prefix = pattern in {"2", "4", "5"}
            needs_date = pattern in {"3", "4", "5"}

            prefix = ""
            date_fmt = ""
            date_source = "today"
            today_str = ""

            if needs_prefix:
                console.print("\n[bold cyan]Enter the prefix string.[/bold cyan]")
                prefix = prompt_prefix()

            if needs_date:
                date_fmt = prompt_date_format()
                date_source = prompt_date_source()
                today_str = datetime.now().strftime(date_fmt)

            console.print("\n[bold cyan]Numbering[/bold cyan]")
            start_num = prompt_start_number()
            padding = prompt_padding()

            new_names = [
                build_new_name(
                    file=f,
                    pattern=pattern,
                    number=start_num + i,
                    padding=padding,
                    prefix=prefix,
                    date_fmt=date_fmt,
                    date_source=date_source,
                    today_str=today_str,
                )
                for i, f in enumerate(files)
            ]

            show_preview(files, new_names)

            console.print(
                "\n[bold yellow]Proceed with rename?[/bold yellow] "
                "[dim]This cannot be undone.[/dim]"
            )
            while True:
                confirm = input("[>] Enter (y/n): ").strip().lower()
                if confirm == "y":
                    break
                if confirm == "n":
                    raise Cancelled()
                console.print("[red]Enter y or n.[/red]")

            console.print()
            success, failed = do_rename(files, new_names)

            summary = (
                f"[bold green]Successful:[/bold green] {success}\n"
                f"[bold red]Failed    :[/bold red] {failed}\n"
                f"[cyan]Folder    :[/cyan] [green]{folder}[/green]"
            )
            console.print(
                Panel(
                    summary,
                    title="[bold yellow]Rename Complete[/bold yellow]",
                    border_style="green" if failed == 0 else "red",
                )
            )

            if prompt_post_action() == "2":
                return

        except Cancelled:
            console.print("\n[yellow]Cancelled.[/yellow]")
            menu = (
                "[bold green]\\[y][/bold green] Try again\n\n"
                "[bold red]\\[n][/bold red] Back to main menu"
            )
            console.print(Panel(menu, title="[bold yellow]What's Next?[/bold yellow]", border_style="white"))
            while True:
                ans = input("\n[>] Select option: ").strip().lower()
                if ans == "y":
                    break
                if ans == "n":
                    return
                console.print("[red]Enter y or n.[/red]")

        except GoBack:
            return


if __name__ == "__main__":
    main()
