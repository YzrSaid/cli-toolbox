#!/usr/bin/env python3
"""
convert_pics.py

A reusable CLI tool for converting images either in batch or individually.

Features:
- Batch conversion
- Individual file conversion
- Dynamic format selection
- Retry flow on error
- Post-conversion menu
"""

from __future__ import annotations

from statistics import mode
import sys
import webbrowser
from pathlib import Path
from typing import Dict

from PIL import Image

# ------------------------------------------------------------
# Application metadata
# ------------------------------------------------------------

# Display name shown in the CLI banner.
APP_NAME = "Picture Converter of CLI Toolbox"

# Current version of the tool.
APP_VERSION = "1.0.0"

# Public links used by the post-conversion menu.
SOURCE_CODE_URL = "https://github.com/YzrSaid/cli-toolbox"
GITHUB_PROFILE_URL = "https://github.com/YzrSaid"

# ------------------------------------------------------------
# Supported image formats
# ------------------------------------------------------------

# Each menu key maps to:
# - label: human-readable format name shown in the menu
# - extensions: accepted input file extensions for that format
# - save_format: Pillow-compatible format name used when saving
# - output_ext: file extension to use for the converted output
FORMATS: Dict[str, Dict[str, object]] = {
    "1": {
        "label": "JPG / JPEG",
        "extensions": (".jpg", ".jpeg"),
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
    },
}


def get_default_output_folder() -> Path:
    """
    Return the default output directory used when the user
    does not provide a custom destination.

    Returns:
        Path: ~/Pictures/converted_pictures
    """
    return Path.home() / "Pictures" / "converted_pictures"


def print_banner() -> None:
    """
    Display the main application banner in the terminal.
    """
    print(f"{APP_NAME} v{APP_VERSION}")


def prompt_non_empty(message: str) -> str:
    """
    Prompt the user until a non-empty input is provided.

    Args:
        message: The message displayed to the user.

    Returns:
        str: A non-empty trimmed string.
    """
    while True:
        value = input(message).strip()
        if value:
            return value
        print("Input cannot be empty. Please try again.\n")


def open_link(url: str, label: str) -> None:
    """
    Attempt to open a URL in the user's default browser.

    If automatic opening fails, the URL is printed so the user
    can open it manually.

    Args:
        url: The target URL to open.
        label: A user-friendly label describing the link.
    """
    print(f"\nOpening {label}...")
    try:
        opened = webbrowser.open(url)
        if not opened:
            print("Could not automatically open browser.")
            print(f"{label}: {url}")
    except Exception:
        print("Could not automatically open browser.")
        print(f"{label}: {url}")


def ensure_valid_input_folder(folder: str) -> Path:
    """
    Validate that the provided path exists and is a directory.

    Args:
        folder: The user-provided folder path.

    Returns:
        Path: A resolved Path object for the input folder.

    Raises:
        FileNotFoundError: If the folder does not exist.
        NotADirectoryError: If the path exists but is not a folder.
    """
    path = Path(folder).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"Input folder does not exist: {path}")

    if not path.is_dir():
        raise NotADirectoryError(f"Input path is not a folder: {path}")

    return path


def ensure_valid_input_file(file_path: str) -> Path:
    """
    Validate that the provided path exists and is a file.

    Args:
        file_path: The user-provided file path.

    Returns:
        Path: A resolved Path object for the input file.

    Raises:
        FileNotFoundError: If the file does not exist or is not a file.
    """
    path = Path(file_path).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"Input file does not exist: {path}")

    if not path.is_file():
        raise FileNotFoundError(f"Input path is not a file: {path}")

    return path


def ensure_output_folder(folder: str | None) -> Path:
    """
    Resolve and create the output directory.

    If no folder is provided, the default output directory is used.

    Args:
        folder: Optional user-provided output folder path.

    Returns:
        Path: A resolved Path object for the output folder.
    """
    if folder and folder.strip():
        output_path = Path(folder).expanduser().resolve()
    else:
        output_path = get_default_output_folder().resolve()

    # Ensure the destination folder exists before writing files.
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def convert_image_for_target(img: Image.Image, output_format: str) -> Image.Image:
    """
    Convert an image into a mode suitable for the target format.

    Why this is needed:
    - JPEG does not support transparency, so transparent images must be
      placed on a solid background.
    - Some formats work better with RGB or RGBA depending on the source.

    Args:
        img: The Pillow image object to prepare.
        output_format: The Pillow output format, e.g. 'JPEG', 'PNG', 'WEBP'.

    Returns:
        Image.Image: A Pillow image converted to a compatible mode.
    """
    if output_format == "JPEG":
        # JPEG does not support transparency, so transparent images must
        # be flattened onto a white background first.
        if img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))

            if img.mode != "RGBA":
                img = img.convert("RGBA")

            background.paste(img, mask=img.split()[-1])
            return background

        return img.convert("RGB")

    if output_format in {"PNG", "WEBP", "TIFF", "GIF", "BMP"}:
        # Preserve alpha-capable formats when possible.
        if img.mode in ("RGBA", "LA"):
            return img

        # Palette-based images are converted to RGBA for better compatibility.
        if img.mode == "P":
            return img.convert("RGBA")

        return img.convert("RGB")

    # Fallback behavior for unexpected or future formats.
    return img.convert("RGB")


def print_mode_menu() -> None:
    """
    Display the conversion mode options.
    """
    print("\nChoose conversion mode:\n")
    print("  1 - Batch conversion")
    print("  2 - Individual conversion")
    print("  3 - Back to main menu")
    print("  4 - Exit")
    print()


def prompt_mode() -> str:
    """
    Prompt the user to choose a conversion mode.

    Returns:
        str: '1', '2', '3', or '4'
    """
    while True:
        print_mode_menu()
        choice = input("Enter your choice (1-4): ").strip()

        if choice in {"1", "2", "3", "4"}:
            return choice

        print("Invalid choice. Please enter 1, 2, 3, or 4.\n")


def print_formats(excluded_key: str | None = None) -> None:
    """
    Display the available image format options.

    Args:
        excluded_key: Optional format key to hide from the menu.
                      This is used so the target format menu does not
                      show the same option chosen as the source format.
    """
    print()

    for key, data in FORMATS.items():
        if key == excluded_key:
            continue
        print(f"  {key} - {data['label']}")

    print()


def prompt_source_format() -> str:
    """
    Prompt the user to select the source image format.

    Returns:
        str: The selected format key.
    """
    while True:
        print("\nChoose the source image format:")
        print_formats()
        choice = input("Enter source format number: ").strip()

        if choice in FORMATS:
            return choice

        print("Invalid choice. Please try again.\n")


def prompt_target_format(excluded_key: str) -> str:
    """
    Prompt the user to select the target image format.

    The chosen source format is excluded from the options so the user
    cannot convert a format into the same format.

    Args:
        excluded_key: The source format key to exclude.

    Returns:
        str: The selected target format key.
    """
    while True:
        print("\nChoose the target image format:")
        print_formats(excluded_key=excluded_key)
        choice = input("Enter target format number: ").strip()

        if choice in FORMATS and choice != excluded_key:
            return choice

        print("Invalid choice. Please choose a different target format.\n")


def convert_single_file(
    input_file: Path,
    output_folder: Path,
    source_key: str,
    target_key: str,
    quality: int = 85,
) -> bool:
    """
    Convert a single image file into the selected target format.

    Args:
        input_file: Full path to the source image.
        output_folder: Folder where the converted file will be saved.
        source_key: Selected source format key from FORMATS.
        target_key: Selected target format key from FORMATS.
        quality: Compression quality used for JPEG and WEBP outputs.

    Returns:
        bool: True if conversion succeeds, otherwise False.
    """
    # Retrieve the target format metadata from the format registry.
    target_info = FORMATS[target_key]
    target_ext = target_info["output_ext"]
    target_format = target_info["save_format"]

    try:
        with Image.open(input_file) as img:
            # Prepare the image mode for the selected output format.
            converted = convert_image_for_target(img, str(target_format))

            # Build the output file path while preserving the original filename.
            output_file = output_folder / f"{input_file.stem}{target_ext}"

            # Save arguments are built dynamically depending on the format.
            save_kwargs = {}

            # JPEG and WEBP support configurable quality.
            if target_format in ("JPEG", "WEBP"):
                save_kwargs["quality"] = quality

            # WEBP supports a compression method; 6 is typically better quality/size balance.
            if target_format == "WEBP":
                save_kwargs["method"] = 6

            # Optimize can help reduce file size for JPEG and PNG.
            if target_format in ("JPEG", "PNG"):
                save_kwargs["optimize"] = True

            converted.save(output_file, str(target_format), **save_kwargs)

        print(f"[OK] {input_file.name} -> {output_file.name}")
        return True

    except Exception as exc:
        print(f"[FAIL] {input_file.name} -> {exc}")
        return False


def batch_convert(
    input_folder: Path,
    output_folder: Path,
    source_key: str,
    target_key: str,
) -> tuple[int, int]:
    """
    Convert all matching files in a folder.

    Only files whose extensions match the selected source format
    are processed. Other files are ignored.

    Args:
        input_folder: Folder containing the source files.
        output_folder: Destination folder for converted files.
        source_key: Selected source format key.
        target_key: Selected target format key.

    Returns:
        tuple[int, int]:
            - successful conversion count
            - failed conversion count
    """
    source_info = FORMATS[source_key]
    source_exts = source_info["extensions"]

    # Collect only files matching the selected source format.
    files = [
        file_path
        for file_path in input_folder.iterdir()
        if file_path.is_file() and file_path.suffix.lower() in source_exts
    ]

    if not files:
        print(f"\nNo supported files found in: {input_folder}")
        print(f"Expected extensions: {', '.join(source_exts)}")
        return (0, 0)

    print("\n" + "=" * 80)
    print("Batch conversion started")
    print(f"Input folder  : {input_folder}")
    print(f"Output folder : {output_folder}")
    print(f"Files found   : {len(files)}")
    print("=" * 80 + "\n")

    success_count = 0
    failed_count = 0

    for file_path in files:
        ok = convert_single_file(file_path, output_folder, source_key, target_key)

        if ok:
            success_count += 1
        else:
            failed_count += 1

    print("\n" + "=" * 80)
    print("Batch conversion complete.")
    print(f"Successful: {success_count}")
    print(f"Failed    : {failed_count}")
    print(f"Saved to  : {output_folder}")
    print("=" * 80)

    return (success_count, failed_count)


def individual_convert(
    input_file: Path,
    output_folder: Path,
    source_key: str,
    target_key: str,
) -> tuple[int, int]:
    """
    Convert a single file and print a summary.

    Args:
        input_file: Full path to the source file.
        output_folder: Destination folder for the converted file.
        source_key: Selected source format key.
        target_key: Selected target format key.

    Returns:
        tuple[int, int]:
            - (1, 0) if successful
            - (0, 1) if failed
    """
    print("\n" + "=" * 80)
    print("Individual conversion started")
    print(f"Input file    : {input_file}")
    print(f"Output folder : {output_folder}")
    print("=" * 80 + "\n")

    ok = convert_single_file(input_file, output_folder, source_key, target_key)

    print("\n" + "=" * 80)
    print("Individual conversion complete.")
    print(f"Successful: {1 if ok else 0}")
    print(f"Failed    : {0 if ok else 1}")
    print(f"Saved to  : {output_folder}")
    print("=" * 80)

    return (1, 0) if ok else (0, 1)


def prompt_next_action() -> str:
    """
    Display the post-conversion menu and collect the user's next action.

    Returns:
        str: A valid action key from '1' to '4'.
    """
    while True:
        print("\nWhat would you like to do next?")
        print("  1 - Convert again")
        print("  2 - View source code")
        print("  3 - Visit GitHub profile")
        print("  4 - Exit")
        print()

        choice = input("Enter your choice (1-4): ").strip()

        if choice in {"1", "2", "3", "4"}:
            return choice

        print("Invalid choice. Please enter 1, 2, 3, or 4.\n")


def handle_post_action() -> bool:
    """
    Handle the user's selected post-conversion action.

    Returns:
        bool:
            - True if the user wants to perform another conversion
            - False if the user chooses to exit
    """
    while True:
        choice = prompt_next_action()

        if choice == "1":
            return True

        if choice == "2":
            open_link(SOURCE_CODE_URL, "source code")

        elif choice == "3":
            open_link(GITHUB_PROFILE_URL, "GitHub profile")

        elif choice == "4":
            print(f"\nThank you for using {APP_NAME}. Goodbye!")
            return False


def collect_conversion_inputs() -> tuple[str, str, str, Path, Path]:
    """
    Run the full interactive input flow for a conversion job.

    Flow:
    - choose mode
    - choose source format
    - choose target format
    - collect input path
    - collect output path
    - validate all values before returning

    Returns:
        tuple[str, str, str, Path, Path]:
            mode, source_key, target_key, input_path, output_path
    """
    while True:
        try:
            print_banner()

            mode = prompt_mode()

            # Handle special options before continuing
            if mode == "3":
                # Return to CLI Toolbox main menu
                raise KeyboardInterrupt

            if mode == "4":
                print("\nThank you for using Picture Converter CLI.")
                raise SystemExit(0)

            source_key = prompt_source_format()
            target_key = prompt_target_format(source_key)

            if mode == "1":
                # Batch mode expects a folder as input.
                input_folder_raw = prompt_non_empty(
                    "\nEnter the absolute input folder path: "
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

            # Individual mode expects a single file as input.
            input_file_raw = prompt_non_empty("\nEnter the absolute input file path: ")
            output_folder_raw = input(
                f"Enter the absolute output folder path\n"
                f"(leave blank to use default: {get_default_output_folder()}): "
            ).strip()

            input_path = ensure_valid_input_file(input_file_raw)

            # Verify that the selected source format matches the actual file extension.
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

        except Exception as exc:
            print(f"\nError: {exc}")
            retry = input("Would you like to try again? (y/n): ").strip().lower()

            if retry != "y":
                raise SystemExit(1)


def interactive_mode() -> None:
    """
    Start and maintain the main interactive application loop.
    """
    while True:
        try:
            mode, source_key, target_key, input_path, output_path = (
                collect_conversion_inputs()
            )

            if mode == "1":
                batch_convert(input_path, output_path, source_key, target_key)
            else:
                individual_convert(input_path, output_path, source_key, target_key)

            if not handle_post_action():
                break

        except KeyboardInterrupt:
            # Used to return to CLI Toolbox main menu
            return


def print_cli_usage() -> None:
    """
    Print the intended usage message for the current version.

    This version is interactive-first, so additional CLI arguments
    are not currently supported.
    """
    print("Usage:")
    print("  python convert_pics.py")
    print("\nThis version uses interactive mode for a guided conversion flow.")


def main() -> None:
    """
    Application entry point.

    Behavior:
    - If arguments are passed, show usage guidance and continue
      into interactive mode.
    - Otherwise, launch the interactive workflow directly.
    """
    if len(sys.argv) > 1:
        print_cli_usage()
        print("\nOpening interactive mode instead...\n")

    interactive_mode()


if __name__ == "__main__":
    main()
