"""
YouTube Downloader Tool

Features:
- Full video or clipped segment download
- Audio-only download (MP3 / M4A)
- Optional custom save path
- Quality selection (video)
- Output preference selection (video)
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


class Cancelled(Exception):
    pass


class GoBack(Exception):
    pass


# ─── Timestamp helpers ────────────────────────────────────────────────────────

def validate_timestamp(ts: str) -> bool:
    """
    Accept MM:SS or H:MM:SS (or HH:MM:SS).
      1:30       → 1 min 30 sec
      10:45      → 10 min 45 sec
      1:02:30    → 1 hr 2 min 30 sec
      01:30:00   → 1 hr 30 min 0 sec
    """
    return bool(re.match(r"^\d{1,2}:\d{2}(:\d{2})?$", ts))


def validate_time_range(time_range: str) -> bool:
    parts = time_range.split("-", 1)
    if len(parts) != 2:
        return False
    return validate_timestamp(parts[0]) and validate_timestamp(parts[1])


def parse_timestamp_to_seconds(timestamp: str) -> int:
    segments = [int(p) for p in timestamp.split(":")]
    if len(segments) == 2:
        minutes, seconds = segments
        return minutes * 60 + seconds
    if len(segments) == 3:
        hours, minutes, seconds = segments
        return hours * 3600 + minutes * 60 + seconds
    raise ValueError("Invalid timestamp format.")


def parse_time_range_to_seconds(time_range: str) -> tuple[int, int]:
    start_text, end_text = time_range.split("-", 1)
    start_sec = parse_timestamp_to_seconds(start_text)
    end_sec = parse_timestamp_to_seconds(end_text)
    if end_sec <= start_sec:
        raise ValueError("End time must be greater than start time.")
    return start_sec, end_sec


# ─── Prompts ──────────────────────────────────────────────────────────────────

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


def get_download_type() -> str:
    """Returns 'video' or 'audio'."""
    menu = (
        "[bold green][1][/bold green] Video\n"
        "[bold green][2][/bold green] Audio only  [dim](MP3 / M4A)[/dim]\n\n"
        "[bold red][0][/bold red] Cancel"
    )
    console.print(Panel(menu, title="[bold yellow]Download Type[/bold yellow]", border_style="white"))
    while True:
        choice = input("\n[>] Select type: ").strip()
        if choice == "0":
            raise Cancelled()
        if choice == "1":
            return "video"
        if choice == "2":
            return "audio"
        console.print("[red]Enter 1 or 2.[/red]")


def prompt_time_range() -> str:
    """
    Loop until the user enters a valid time range or leaves it blank (meaning full download).
    Returns the raw time range string, e.g. '1:30:00-1:45:00'.
    """
    hint = (
        "[dim]Format — MM:SS or H:MM:SS[/dim]\n"
        "[dim]Examples:[/dim]\n"
        "[dim]  2:30-5:00       → from 2 min 30 sec to 5 min 0 sec[/dim]\n"
        "[dim]  1:30:00-1:45:00 → from 1 hr 30 min to 1 hr 45 min[/dim]\n"
        "[dim]  0:00:30-0:02:00 → from 30 sec to 2 min[/dim]"
    )
    console.print(Panel(hint, title="[bold yellow]Clip Range[/bold yellow]", border_style="bright_black"))

    while True:
        time_range = input("\n[>] Timestamp (start-end, or 0 to cancel): ").strip()

        if time_range == "0":
            raise Cancelled()

        if not validate_time_range(time_range):
            console.print(
                "[red]Invalid format.[/red] "
                "[dim]Use MM:SS-MM:SS or H:MM:SS-H:MM:SS, e.g. 1:30:00-1:45:00[/dim]"
            )
            continue

        try:
            parse_time_range_to_seconds(time_range)
            return time_range
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")


def prompt_clip_choice() -> bool:
    """Returns True if the user wants a clip."""
    console.print("\n[bold cyan]Download a specific clip?[/bold cyan]")
    while True:
        choice = input("[>] Enter (y/n/0 to cancel): ").strip().lower()
        if choice == "0":
            raise Cancelled()
        if choice == "y":
            return True
        if choice == "n":
            return False
        console.print("[red]Enter y, n, or 0 to cancel.[/red]")


def get_quality_choice() -> tuple[str, str, str]:
    """Returns format_selector, sort_selector, quality_label."""
    menu = (
        "[bold green][1][/bold green] Best quality\n"
        "[bold green][2][/bold green] 1080p\n"
        "[bold green][3][/bold green] 720p\n"
        "[bold green][4][/bold green] 480p\n"
        "[bold green][5][/bold green] 360p\n\n"
        "[bold red][0][/bold red] Cancel"
    )
    console.print(Panel(menu, title="[bold yellow]Video Quality[/bold yellow]", border_style="white"))

    choice = input("\n[>] Select quality: ").strip()
    if choice == "0":
        raise Cancelled()
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
    """Returns output_preference, output_label."""
    menu = (
        "[bold green][1][/bold green] Preferred format\n"
        "[dim]    Faster, but may be webm/mkv depending on source[/dim]\n\n"
        "[bold green][2][/bold green] MP4\n"
        "[dim]    May take longer due to remuxing[/dim]\n\n"
        "[bold red][0][/bold red] Cancel"
    )
    console.print(Panel(menu, title="[bold yellow]Output Format[/bold yellow]", border_style="white"))

    choice = input("\n[>] Select output format: ").strip()
    if choice == "0":
        raise Cancelled()
    if choice == "2":
        return "mp4", "MP4"
    return "preferred", "Preferred format"


def get_audio_format_choice() -> tuple[str, str]:
    """Returns codec, label."""
    menu = (
        "[bold green][1][/bold green] MP3   [dim](requires ffmpeg)[/dim]\n"
        "[bold green][2][/bold green] M4A   [dim](no re-encoding — faster, no ffmpeg needed)[/dim]\n\n"
        "[bold red][0][/bold red] Cancel"
    )
    console.print(Panel(menu, title="[bold yellow]Audio Format[/bold yellow]", border_style="white"))

    choice = input("\n[>] Select format: ").strip()
    if choice == "0":
        raise Cancelled()
    if choice == "2":
        return "m4a", "M4A"
    return "mp3", "MP3"


# ─── yt-dlp option builders ───────────────────────────────────────────────────

class QuietLogger:
    def debug(self, msg: str) -> None:
        return

    def warning(self, msg: str) -> None:
        return

    def error(self, msg: str) -> None:
        console.print(f"\n[bold red]Error:[/bold red] {msg}")


def _base_opts(save_dir: str, output_template: str) -> dict:
    return {
        "paths": {"home": save_dir},
        "outtmpl": {"default": output_template},
        "logger": QuietLogger(),
        "noprogress": True,
        "quiet": True,
        "no_warnings": True,
    }


def _apply_time_range(ydl_opts: dict, time_range: str) -> dict:
    start_sec, end_sec = parse_time_range_to_seconds(time_range)
    ydl_opts["download_ranges"] = yt_dlp.utils.download_range_func(
        None, [(start_sec, end_sec)]
    )
    ydl_opts["force_keyframes_at_cuts"] = True
    return ydl_opts


def build_video_opts(
    save_dir: str,
    output_template: str,
    format_selector: str,
    sort_selector: str,
    output_preference: str,
    time_range: str | None = None,
) -> dict:
    opts = _base_opts(save_dir, output_template)
    opts["format"] = format_selector
    opts["format_sort"] = [sort_selector]

    if output_preference == "mp4":
        opts["format_sort"] = [sort_selector, "ext:mp4:m4a"]
        opts["merge_output_format"] = "mp4"
        opts["remuxvideo"] = "mp4"

    if time_range:
        opts = _apply_time_range(opts, time_range)

    return opts


def build_audio_opts(
    save_dir: str,
    output_template: str,
    codec: str,
    time_range: str | None = None,
) -> dict:
    opts = _base_opts(save_dir, output_template)

    if codec == "mp3":
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    else:  # m4a — no re-encoding, no ffmpeg required
        opts["format"] = "bestaudio[ext=m4a]/bestaudio[ext=mp4]/bestaudio"

    if time_range:
        opts = _apply_time_range(opts, time_range)

    return opts


# ─── Download runner ──────────────────────────────────────────────────────────

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


# ─── Entry point ──────────────────────────────────────────────────────────────

def prompt_post_action() -> str:
    menu = (
        "[bold green][1][/bold green] Download another\n\n"
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


def main() -> None:
    console.print(
        Panel(
            "[bold bright_green]YouTube Downloader[/bold bright_green]",
            border_style="green",
        )
    )

    while True:
        try:
            console.print("[dim]Enter q to go back to main menu.[/dim]")
            while True:
                url = input("Paste the YouTube video link: ").strip()
                if url.lower() == "q":
                    raise GoBack()
                if url:
                    break
                console.print("[red]Please paste a YouTube link.[/red]")

            save_dir = get_save_directory()
            download_type = get_download_type()
            want_clip = prompt_clip_choice()
            time_range = prompt_time_range() if want_clip else None

            if download_type == "audio":
                codec, codec_label = get_audio_format_choice()

                summary_lines = (
                    f"[cyan][>][/cyan] Type    : [green]Audio only[/green]\n"
                    f"[cyan][>][/cyan] Format  : [green]{codec_label}[/green]\n"
                    f"[cyan][>][/cyan] Save to : [green]{save_dir}[/green]"
                    + (f"\n[cyan][>][/cyan] Range   : [green]{time_range}[/green]" if time_range else "")
                )
                console.print(Panel(summary_lines, title="[bold yellow]Download Summary[/bold yellow]", border_style="bright_black"))

                label = f"audio clip ({time_range})" if time_range else "audio"
                console.print(f"\n[bold cyan]Preparing {label} download...[/bold cyan]\n")

                template = "clip_%(title)s.%(ext)s" if time_range else "%(title)s.%(ext)s"
                opts = build_audio_opts(save_dir, template, codec, time_range)
                run_download(url, opts, save_dir)

            else:
                format_selector, sort_selector, quality_label = get_quality_choice()
                output_preference, output_label = get_output_preference()

                summary_lines = (
                    f"[cyan][>][/cyan] Type    : [green]Video[/green]\n"
                    f"[cyan][>][/cyan] Quality : [green]{quality_label}[/green]\n"
                    f"[cyan][>][/cyan] Output  : [green]{output_label}[/green]\n"
                    f"[cyan][>][/cyan] Save to : [green]{save_dir}[/green]"
                    + (f"\n[cyan][>][/cyan] Range   : [green]{time_range}[/green]" if time_range else "")
                )
                console.print(Panel(summary_lines, title="[bold yellow]Download Summary[/bold yellow]", border_style="bright_black"))

                label = f"clip ({time_range})" if time_range else "full video"
                console.print(f"\n[bold cyan]Preparing {label} download...[/bold cyan]\n")

                template = "clip_%(title)s.%(ext)s" if time_range else "%(title)s.%(ext)s"
                opts = build_video_opts(save_dir, template, format_selector, sort_selector, output_preference, time_range)
                run_download(url, opts, save_dir)

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
