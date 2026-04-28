#!/usr/bin/env python3
"""
A reusable CLI tool for converting images either in batch or individually.

Features:
- Batch conversion
- Individual file conversion
- Dynamic format selection
- Retry flow on error
- Post-conversion menu
"""

from __future__ import annotations

import base64
from io import BytesIO
import sys
import webbrowser
from pathlib import Path
from typing import Dict

from PIL import Image
from rich.console import Console
from rich.panel import Panel

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
    HEIF_SUPPORT_AVAILABLE = True
except Exception:
    HEIF_SUPPORT_AVAILABLE = False


class Cancelled(Exception):
    pass


class GoBack(Exception):
    pass

# ------------------------------------------------------------
# Application metadata
# ------------------------------------------------------------


APP_NAME = "Image Converter"
APP_VERSION = "1.2.0"

SOURCE_CODE_URL = "https://github.com/YzrSaid/cli-toolbox"
GITHUB_PROFILE_URL = "https://github.com/YzrSaid"

console = Console()

# ------------------------------------------------------------
# Supported image formats
# ------------------------------------------------------------

FORMATS: Dict[str, Dict[str, object]] = {
    "1": {
        "label": "JPG / JPEG / JFIF",
        "extensions": (".jpg", ".jpeg", ".jfif"),
        "save_format": "JPEG",
        "output_ext": ".jpg",
    },
    "2": {
        "label": "PNG",
        "extensions": (".png",),
        "save_format": "PNG",
        "output_ext": ".png",
    },
    "3": {
        "label": "WEBP",
        "extensions": (".webp",),
        "save_format": "WEBP",
        "output_ext": ".webp",
    },
    "4": {
        "label": "BMP",
        "extensions": (".bmp",),
        "save_format": "BMP",
        "output_ext": ".bmp",
    },
    "5": {
        "label": "TIFF",
        "extensions": (".tiff", ".tif"),
        "save_format": "TIFF",
        "output_ext": ".tiff",
    },
    "6": {
        "label": "GIF",
        "extensions": (".gif",),
        "save_format": "GIF",
        "output_ext": ".gif",
        "source": True,
        "target": True,
    },
    "7": {
        "label": "HEIC / HEIF",
        "extensions": (".heic", ".heif"),
        "save_format": "HEIC",
        "output_ext": ".heic",
        "source": True,
        "target": False,
    },
    "8": {
        "label": "ICO",
        "extensions": (".ico",),
        "save_format": "ICO",
        "output_ext": ".ico",
        "source": True,
        "target": True,
    },
    "9": {
        "label": "SVG",
        "extensions": (".svg",),
        "save_format": "SVG",
        "output_ext": ".svg",
        "source": False,
        "target": True,
    },
}

for item in FORMATS.values():
    item.setdefault("source", True)
    item.setdefault("target", True)


def get_default_output_folder() -> Path:
    return Path.home() / "Pictures" / "converted_pictures"


def print_banner() -> None:
    console.print(
        Panel(
            f"[bold bright_green]{APP_NAME}[/bold bright_green]  [dim]v{APP_VERSION}[/dim]",
            border_style="green",
        )
    )


def prompt_non_empty(message: str) -> str:
    console.print("[dim]Enter q to cancel.[/dim]")
    while True:
        value = input(message + " ").strip()
        if value.lower() == "q":
            raise GoBack()
        if value:
            return value
        console.print("[red]Please enter a valid path.[/red]")


def open_link(url: str, label: str) -> None:
    console.print(f"\n[bold cyan]Opening {label}...[/bold cyan]")
    try:
        opened = webbrowser.open(url)
        if not opened:
            console.print("[red]Could not automatically open browser.[/red]")
            console.print(f"{label}: [green]{url}[/green]")
    except Exception:
        console.print("[red]Could not automatically open browser.[/red]")
        console.print(f"{label}: [green]{url}[/green]")


def ensure_valid_input_folder(folder: str) -> Path:
    path = Path(folder).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"Input folder does not exist: {path}")

    if not path.is_dir():
        raise NotADirectoryError(f"Input path is not a folder: {path}")

    return path


def ensure_valid_input_file(file_path: str) -> Path:
    path = Path(file_path).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"Input file does not exist: {path}")

    if not path.is_file():
        raise FileNotFoundError(f"Input path is not a file: {path}")

    return path


def ensure_output_folder(folder: str | None) -> Path:
    if folder and folder.strip():
        output_path = Path(folder).expanduser().resolve()
    else:
        output_path = get_default_output_folder().resolve()

    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def convert_image_for_target(img: Image.Image, output_format: str) -> Image.Image:
    if output_format == "JPEG":
        if img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))

            if img.mode != "RGBA":
                img = img.convert("RGBA")

            background.paste(img, mask=img.split()[-1])
            return background

        return img.convert("RGB")

    if output_format == "ICO":
        if img.mode in ("RGBA", "LA"):
            return img.convert("RGBA")
        if img.mode == "P":
            return img.convert("RGBA")
        return img.convert("RGBA")

    if output_format in {"PNG", "WEBP", "TIFF", "GIF", "BMP"}:
        if img.mode in ("RGBA", "LA"):
            return img

        if img.mode == "P":
            return img.convert("RGBA")

        return img.convert("RGB")

    return img.convert("RGB")


def save_as_svg_with_embedded_png(img: Image.Image, output_file: Path) -> None:
    rendered = img.convert("RGBA")
    png_buffer = BytesIO()
    rendered.save(png_buffer, "PNG", optimize=True)

    encoded = base64.b64encode(png_buffer.getvalue()).decode("ascii")
    width, height = rendered.size

    svg_content = (
        f"<svg xmlns=\"http://www.w3.org/2000/svg\" "
        f"width=\"{width}\" height=\"{height}\" "
        f"viewBox=\"0 0 {width} {height}\">"
        f"<image width=\"{width}\" height=\"{height}\" "
        f"href=\"data:image/png;base64,{encoded}\"/></svg>"
    )

    output_file.write_text(svg_content, encoding="utf-8")


def get_format_choices(
    *,
    for_target: bool,
    excluded_key: str | None = None,
) -> Dict[str, Dict[str, object]]:
    flag_name = "target" if for_target else "source"

    return {
        key: data
        for key, data in FORMATS.items()
        if bool(data.get(flag_name)) and key != excluded_key
    }


def print_mode_menu() -> None:
    menu = (
        "[bold green][1][/bold green] Batch conversion\n"
        "[bold green][2][/bold green] Individual conversion\n"
        "[bold green][3][/bold green] Back to main menu\n\n"
        "[bold red][4][/bold red] Exit"
    )
    console.print(
        Panel(
            menu,
            title="[bold yellow]Conversion Mode[/bold yellow]",
            border_style="white",
        )
    )


def prompt_mode() -> str:
    while True:
        print_mode_menu()
        choice = input("\n[>] Enter your choice (1-4): ").strip()

        if choice in {"1", "2", "3", "4"}:
            return choice

        console.print(
            "[red]Invalid choice. Please enter 1, 2, 3, or 4.[/red]\n")


def print_formats(
    *,
    for_target: bool,
    excluded_key: str | None = None,
) -> None:
    choices = get_format_choices(
        for_target=for_target, excluded_key=excluded_key)
    console.print()
    for key, data in choices.items():
        console.print(f"  [bold green][{key}][/bold green] {data['label']}")
    console.print(f"  [bold red][0][/bold red] Cancel")
    console.print()


def prompt_source_format() -> str:
    while True:
        console.print(
            "\n[bold cyan]Choose the source image format:[/bold cyan]")
        print_formats(for_target=False)
        choice = input("[>] Enter source format number: ").strip()

        if choice == "0":
            raise Cancelled()

        if choice in get_format_choices(for_target=False):
            if choice == "7" and not HEIF_SUPPORT_AVAILABLE:
                console.print(
                    "[red]HEIC/HEIF support is unavailable. Install dependencies with:[/red]\n"
                    "[dim]pip install -r requirements.txt[/dim]\n"
                )
                continue
            return choice

        console.print("[red]Invalid choice. Please try again.[/red]\n")


def prompt_target_format(excluded_key: str) -> str:
    while True:
        console.print(
            "\n[bold cyan]Choose the target image format:[/bold cyan]")
        print_formats(for_target=True, excluded_key=excluded_key)
        choice = input("[>] Enter target format number: ").strip()

        if choice == "0":
            raise Cancelled()

        if choice in get_format_choices(for_target=True, excluded_key=excluded_key):
            return choice

        console.print(
            "[red]Invalid choice. Please choose a different target format.[/red]\n")


def convert_single_file(
    input_file: Path,
    output_folder: Path,
    source_key: str,
    target_key: str,
    quality: int = 85,
) -> bool:
    target_info = FORMATS[target_key]
    target_ext = target_info["output_ext"]
    target_format = target_info["save_format"]

    try:
        with Image.open(input_file) as img:
            output_file = output_folder / f"{input_file.stem}{target_ext}"

            if target_format == "SVG":
                save_as_svg_with_embedded_png(img, output_file)
                console.print(
                    f"  [bold green][OK][/bold green]   {input_file.name} [dim]->[/dim] {output_file.name}")
                return True

            converted = convert_image_for_target(img, str(target_format))

            save_kwargs = {}

            if target_format in ("JPEG", "WEBP"):
                save_kwargs["quality"] = quality

            if target_format == "WEBP":
                save_kwargs["method"] = 6

            if target_format in ("JPEG", "PNG"):
                save_kwargs["optimize"] = True

            if target_format == "ICO":
                save_kwargs["sizes"] = [
                    (16, 16),
                    (24, 24),
                    (32, 32),
                    (48, 48),
                    (64, 64),
                    (128, 128),
                    (256, 256),
                ]

            converted.save(output_file, str(target_format), **save_kwargs)

        console.print(
            f"  [bold green][OK][/bold green]   {input_file.name} [dim]->[/dim] {output_file.name}")
        return True

    except Exception as exc:
        console.print(
            f"  [bold red][FAIL][/bold red] {input_file.name} [dim]->[/dim] {exc}")
        return False


def batch_convert(
    input_folder: Path,
    output_folder: Path,
    source_key: str,
    target_key: str,
) -> tuple[int, int]:
    source_info = FORMATS[source_key]
    source_exts = source_info["extensions"]

    files = [
        file_path
        for file_path in input_folder.iterdir()
        if file_path.is_file() and file_path.suffix.lower() in source_exts
    ]

    if not files:
        console.print(
            f"\n[yellow]No supported files found in:[/yellow] {input_folder}")
        console.print(
            f"[dim]Expected extensions: {', '.join(source_exts)}[/dim]")
        return (0, 0)

    header = (
        f"[cyan][>][/cyan] Input folder  : [green]{input_folder}[/green]\n"
        f"[cyan][>][/cyan] Output folder : [green]{output_folder}[/green]\n"
        f"[cyan][>][/cyan] Files found   : [bold white]{len(files)}[/bold white]"
    )
    console.print(
        Panel(
            header, title="[bold yellow]Batch Conversion[/bold yellow]", border_style="cyan")
    )
    console.print()

    success_count = 0
    failed_count = 0

    for file_path in files:
        ok = convert_single_file(
            file_path, output_folder, source_key, target_key)

        if ok:
            success_count += 1
        else:
            failed_count += 1

    summary = (
        f"[bold green]Successful:[/bold green] {success_count}\n"
        f"[bold red]Failed    :[/bold red] {failed_count}\n"
        f"[cyan]Saved to  :[/cyan] [green]{output_folder}[/green]"
    )
    console.print(
        Panel(
            summary, title="[bold yellow]Batch Complete[/bold yellow]", border_style="green")
    )

    return (success_count, failed_count)


def individual_convert(
    input_file: Path,
    output_folder: Path,
    source_key: str,
    target_key: str,
) -> tuple[int, int]:
    header = (
        f"[cyan][>][/cyan] Input file    : [green]{input_file}[/green]\n"
        f"[cyan][>][/cyan] Output folder : [green]{output_folder}[/green]"
    )
    console.print(
        Panel(
            header, title="[bold yellow]Individual Conversion[/bold yellow]", border_style="cyan")
    )
    console.print()

    ok = convert_single_file(input_file, output_folder, source_key, target_key)

    summary = (
        f"[bold green]Successful:[/bold green] {1 if ok else 0}\n"
        f"[bold red]Failed    :[/bold red] {0 if ok else 1}\n"
        f"[cyan]Saved to  :[/cyan] [green]{output_folder}[/green]"
    )
    console.print(
        Panel(
            summary,
            title="[bold yellow]Conversion Complete[/bold yellow]",
            border_style="green" if ok else "red",
        )
    )

    return (1, 0) if ok else (0, 1)


def handle_post_action() -> bool:
    menu = (
        "[bold green][1][/bold green] Convert again\n\n"
        "[bold red][2][/bold red] Back to main menu"
    )
    console.print(
        Panel(
            menu,
            title="[bold yellow]What's Next?[/bold yellow]",
            border_style="white",
        )
    )

    while True:
        choice = input("\n[>] Enter your choice: ").strip()

        if choice == "1":
            return True
        if choice == "2":
            return False

        console.print("[red]Enter 1 or 2.[/red]\n")


def collect_conversion_inputs() -> tuple[str, str, str, Path, Path]:
    while True:
        try:
            print_banner()

            mode = prompt_mode()

            if mode == "3":
                raise KeyboardInterrupt

            if mode == "4":
                console.print(
                    "\n[bold cyan]Thank you for using Image Converter.[/bold cyan]")
                raise SystemExit(0)

            source_key = prompt_source_format()
            target_key = prompt_target_format(source_key)

            if mode == "1":
                input_folder_raw = prompt_non_empty(
                    "Enter the absolute input folder path: "
                )
                output_folder_raw = input(
                    f"Enter the absolute output folder path\n"
                    f"(leave blank to use default: {get_default_output_folder()}): "
                ).strip()

                input_path = ensure_valid_input_folder(input_folder_raw)
                output_path = ensure_output_folder(
                    output_folder_raw if output_folder_raw else None
                )

                return mode, source_key, target_key, input_path, output_path

            input_file_raw = prompt_non_empty(
                "\nEnter the absolute input file path: ")
            output_folder_raw = input(
                f"Enter the absolute output folder path\n"
                f"(leave blank to use default: {get_default_output_folder()}): "
            ).strip()

            input_path = ensure_valid_input_file(input_file_raw)

            allowed_exts = FORMATS[source_key]["extensions"]
            if input_path.suffix.lower() not in allowed_exts:
                raise ValueError(
                    f"The selected source format does not match the file.\n"
                    f"Expected one of: {', '.join(allowed_exts)}\n"
                    f"Received: {input_path.suffix.lower()}"
                )

            output_path = ensure_output_folder(
                output_folder_raw if output_folder_raw else None
            )

            return mode, source_key, target_key, input_path, output_path

        except (Cancelled, GoBack):
            raise
        except Exception as exc:
            console.print(f"\n[bold red]Error:[/bold red] {exc}")
            retry = input(
                "Would you like to try again? (y/n): ").strip().lower()

            if retry != "y":
                raise SystemExit(1)


def interactive_mode() -> None:
    while True:
        try:
            mode, source_key, target_key, input_path, output_path = (
                collect_conversion_inputs()
            )

            if mode == "1":
                batch_convert(input_path, output_path, source_key, target_key)
            else:
                individual_convert(input_path, output_path,
                                   source_key, target_key)

            if not handle_post_action():
                break

        except GoBack:
            return

        except Cancelled:
            console.print("\n[yellow]Cancelled.[/yellow]")
            menu = (
                "[bold green]\\[y][/bold green] Try again\n\n"
                "[bold red]\\[n][/bold red] Back to main menu"
            )
            console.print(Panel(
                menu, title="[bold yellow]What's Next?[/bold yellow]", border_style="white"))
            while True:
                ans = input("\n[>] Select option: ").strip().lower()
                if ans == "y":
                    break
                if ans == "n":
                    return
                console.print("[red]Enter y or n.[/red]")

        except KeyboardInterrupt:
            return


def print_cli_usage() -> None:
    console.print("[bold cyan]Usage:[/bold cyan]")
    console.print("  python convert_pics.py")
    console.print(
        "\n[dim]This version uses interactive mode for a guided conversion flow.[/dim]")


def main() -> None:
    if len(sys.argv) > 1:
        print_cli_usage()
        console.print("\n[dim]Opening interactive mode instead...[/dim]\n")

    interactive_mode()


if __name__ == "__main__":
    main()
