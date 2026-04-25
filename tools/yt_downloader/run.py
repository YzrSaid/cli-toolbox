"""
YouTube Downloader Tool

Features:
- Full video or clipped segment download
- Optional custom save path
- Quality selection
- Output preference selection:
    - Preferred/original compatible format (faster)
    - MP4 (may take longer)
- Rich progress display
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import yt_dlp
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

console = Console()


def validate_time_range(time_range: str) -> bool:
    """
    Accept:
    2:00-2:11
    12:34-15:20
    1:02:03-1:05:10
    """
    pattern = r"^\d{1,2}:\d{2}(?::\d{2})?-\d{1,2}:\d{2}(?::\d{2})?$"
    return bool(re.match(pattern, time_range))


def parse_timestamp_to_seconds(timestamp: str) -> int:
    """
    Convert:
    2:00 -> 120
    12:34 -> 754
    1:02:03 -> 3723
    """
    parts = [int(part) for part in timestamp.split(":")]

    if len(parts) == 2:
        minutes, seconds = parts
        return minutes * 60 + seconds

    if len(parts) == 3:
        hours, minutes, seconds = parts
        return hours * 3600 + minutes * 60 + seconds

    raise ValueError("Invalid timestamp format")


def parse_time_range_to_seconds(time_range: str) -> tuple[int, int]:
    """
    Convert:
    2:00-3:00 -> (120, 180)
    """
    start_text, end_text = time_range.split("-")
    start_seconds = parse_timestamp_to_seconds(start_text)
    end_seconds = parse_timestamp_to_seconds(end_text)

    if end_seconds <= start_seconds:
        raise ValueError("End time must be greater than start time.")

    return start_seconds, end_seconds


def get_save_directory() -> str:
    console.print("\n[bold cyan]Where do you want to save the file?[/bold cyan]")
    console.print("[dim]Leave blank to save in the same folder where you ran main.py[/dim]")
    save_path = input("Save path: ").strip()

    if not save_path:
        return os.getcwd()

    output_dir = Path(save_path).expanduser().resolve()

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        console.print("[red]Invalid path. Using current working directory instead.[/red]")
        return os.getcwd()

    return str(output_dir)


def get_quality_choice() -> tuple[str, str, str]:
    """
    Returns:
        format_selector, sort_selector, quality_label
    """
    menu = (
        "[bold green][1][/bold green] Best quality\n"
        "[bold green][2][/bold green] 1080p\n"
        "[bold green][3][/bold green] 720p\n"
        "[bold green][4][/bold green] 480p\n"
        "[bold green][5][/bold green] 360p"
    )
    console.print(
        Panel(menu, title="[bold yellow]Video Quality[/bold yellow]", border_style="white")
    )

    choice = input("\n[>] Select quality: ").strip()

    format_selector = "bv*+ba/b"

    if choice == "2":
        return format_selector, "res:1080", "1080p"
    if choice == "3":
        return format_selector, "res:720", "720p"
    if choice == "4":
        return format_selector, "res:480", "480p"
    if choice == "5":
        return format_selector, "res:360", "360p"

    return format_selector, "quality", "Best quality"


def get_output_preference() -> tuple[str, str]:
    """
    Returns:
        output_preference, output_label
    """
    menu = (
        "[bold green][1][/bold green] Preferred format\n"
        "[dim]    Faster, but may be webm/mkv depending on source[/dim]\n\n"
        "[bold green][2][/bold green] MP4\n"
        "[dim]    Note: MP4 may take longer than preferred formats[/dim]"
    )
    console.print(
        Panel(menu, title="[bold yellow]Output Format[/bold yellow]", border_style="white")
    )

    choice = input("\n[>] Select output format: ").strip()

    if choice == "2":
        return "mp4", "MP4"

    return "preferred", "Preferred format"


class QuietLogger:
    def debug(self, msg: str) -> None:
        return

    def warning(self, msg: str) -> None:
        return

    def error(self, msg: str) -> None:
        console.print(f"\n[bold red]Error:[/bold red] {msg}")


def build_ydl_opts(
    save_dir: str,
    output_template: str,
    format_selector: str,
    sort_selector: str,
    output_preference: str,
    time_range: str | None = None,
) -> dict:
    ydl_opts: dict = {
        "paths": {"home": save_dir},
        "outtmpl": {"default": output_template},
        "format": format_selector,
        "logger": QuietLogger(),
        "noprogress": True,
        "quiet": True,
        "no_warnings": True,
        "format_sort": [sort_selector],
    }

    if time_range:
        start_seconds, end_seconds = parse_time_range_to_seconds(time_range)
        ydl_opts["download_ranges"] = yt_dlp.utils.download_range_func(
            None,
            [(start_seconds, end_seconds)],
        )
        ydl_opts["force_keyframes_at_cuts"] = True

    if output_preference == "mp4":
        ydl_opts["format_sort"] = [sort_selector, "ext:mp4:m4a"]
        ydl_opts["merge_output_format"] = "mp4"
        ydl_opts["remuxvideo"] = "mp4"

    return ydl_opts


def run_download(url: str, ydl_opts: dict, save_dir: str) -> None:
    with Progress(
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=True,
    ) as progress:
        tasks: dict[str, int] = {}

        def hook(data: dict) -> None:
            status = data.get("status", "")
            filename = Path(data.get("filename", "file")).name

            if status == "downloading":
                total = data.get("total_bytes") or data.get("total_bytes_estimate", 0) or 0
                downloaded = data.get("downloaded_bytes", 0)

                if filename not in tasks:
                    task_id = progress.add_task(f"[cyan]{filename}[/cyan]", total=total or None)
                    tasks[filename] = task_id
                else:
                    task_id = tasks[filename]

                progress.update(task_id, completed=downloaded, total=total or None)

            elif status == "finished":
                if filename in tasks:
                    progress.update(
                        tasks[filename],
                        description=f"[green]Done[/green] {filename}",
                    )

        ydl_opts = {**ydl_opts, "progress_hooks": [hook]}

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        except Exception as exc:
            console.print(f"\n[bold red]Download failed:[/bold red] {exc}")
            return

    console.print("[bold green]Download complete![/bold green]")
    console.print(f"[cyan]Saved to:[/cyan] [green]{save_dir}[/green]")


def download_full_video(
    url: str,
    save_dir: str,
    format_selector: str,
    sort_selector: str,
    output_preference: str,
) -> None:
    console.print("\n[bold cyan]Preparing full video download...[/bold cyan]\n")

    ydl_opts = build_ydl_opts(
        save_dir=save_dir,
        output_template="%(title)s.%(ext)s",
        format_selector=format_selector,
        sort_selector=sort_selector,
        output_preference=output_preference,
    )

    run_download(url, ydl_opts, save_dir)


def download_clip(
    url: str,
    time_range: str,
    save_dir: str,
    format_selector: str,
    sort_selector: str,
    output_preference: str,
) -> None:
    console.print(f"\n[bold cyan]Preparing clip download[/bold cyan] [dim]({time_range})[/dim]...\n")

    ydl_opts = build_ydl_opts(
        save_dir=save_dir,
        output_template="clip_%(title)s.%(ext)s",
        format_selector=format_selector,
        sort_selector=sort_selector,
        output_preference=output_preference,
        time_range=time_range,
    )

    run_download(url, ydl_opts, save_dir)


def main() -> None:
    console.print(
        Panel(
            "[bold bright_green]YouTube Downloader[/bold bright_green]",
            border_style="green",
        )
    )

    url = input("\nPaste the YouTube video link: ").strip()

    if not url:
        console.print("\n[red]Invalid link.[/red]")
        input("Press Enter to return...")
        return

    save_dir = get_save_directory()

    console.print("\n[bold cyan]Download specific part only?[/bold cyan]")
    choice = input("Enter (y/n): ").strip().lower()

    time_range = ""
    if choice == "y":
        console.print("\n[bold cyan]Enter the time range.[/bold cyan]")
        console.print("[dim]Example format: 2:00-2:11[/dim]")
        console.print("[dim]You can also use: 1:02:03-1:02:20[/dim]\n")

        time_range = input("Timestamp: ").strip()

        if not validate_time_range(time_range):
            console.print("\n[red]Invalid format.[/red]")
            console.print("[dim]Correct examples:[/dim]")
            console.print("[dim]  2:00-2:11[/dim]")
            console.print("[dim]  1:02:03-1:02:20[/dim]")
            input("\nPress Enter to return...")
            return

        try:
            parse_time_range_to_seconds(time_range)
        except ValueError as exc:
            console.print(f"\n[red]Invalid time range:[/red] {exc}")
            input("\nPress Enter to return...")
            return

    elif choice != "n":
        console.print("\n[red]Invalid choice. Please enter y or n.[/red]")
        input("\nPress Enter to return...")
        return

    format_selector, sort_selector, quality_label = get_quality_choice()
    output_preference, output_label = get_output_preference()

    summary = (
        f"[cyan][>][/cyan] Quality : [green]{quality_label}[/green]\n"
        f"[cyan][>][/cyan] Output  : [green]{output_label}[/green]\n"
        f"[cyan][>][/cyan] Save to : [green]{save_dir}[/green]"
        + (f"\n[cyan][>][/cyan] Range   : [green]{time_range}[/green]" if choice == "y" else "")
    )
    console.print(
        Panel(summary, title="[bold yellow]Download Summary[/bold yellow]", border_style="bright_black")
    )

    if choice == "y":
        download_clip(
            url=url,
            time_range=time_range,
            save_dir=save_dir,
            format_selector=format_selector,
            sort_selector=sort_selector,
            output_preference=output_preference,
        )
    else:
        download_full_video(
            url=url,
            save_dir=save_dir,
            format_selector=format_selector,
            sort_selector=sort_selector,
            output_preference=output_preference,
        )

    input("\nPress Enter to return to menu...")


if __name__ == "__main__":
    main()
