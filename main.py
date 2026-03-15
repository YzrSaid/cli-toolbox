#!/usr/bin/env python3
"""
CLI Toolbox Launcher

This script serves as the main entry point for the CLI Toolbox project.
It allows users to select and launch different tools from a centralized menu.
"""

from __future__ import annotations

import os
import webbrowser

from tools.image_converter.run import main as image_converter

PROJECT_NAME = "CLI Toolbox"
DEVELOPER = "Mohammad Aldrin Said"
SOURCE_CODE_URL = "https://github.com/YzrSaid/cli-toolbox"


def clear_screen() -> None:
    """
    Clear the terminal screen for a cleaner CLI experience.
    Supports Windows, Linux, and macOS.
    """
    os.system("cls" if os.name == "nt" else "clear")


def print_banner() -> None:
    """
    Display the welcome banner for the CLI Toolbox launcher.
    """
    print(f"Welcome to {PROJECT_NAME}\n")
    print(f"Developer: {DEVELOPER}")
    print("© 2026 | All Rights Reserved.")


def print_menu() -> None:
    """
    Display the list of available tools and options.
    """
    print("\nAvailable Options:\n")
    print(" 1 - Image Converter")
    print(" 2 - View Source Code")
    print(" 3 - Exit\n")


def open_source_code() -> None:
    """
    Open the CLI Toolbox GitHub repository in the user's browser.
    """
    print("\nOpening source code repository...\n")

    try:
        opened = webbrowser.open(SOURCE_CODE_URL)

        if not opened:
            print("Unable to open browser automatically.")
            print(f"Source Code: {SOURCE_CODE_URL}")

    except Exception:
        print("Unable to open browser automatically.")
        print(f"Source Code: {SOURCE_CODE_URL}")


def main() -> None:
    """
    Run the CLI Toolbox launcher loop.
    """
    while True:
        clear_screen()
        print_banner()
        print_menu()

        choice = input("Select an option: ").strip()

        if choice == "1":
            clear_screen()
            image_converter()

        elif choice == "2":
            open_source_code()
            input("\nPress Enter to return to menu...")

        elif choice == "3":
            print("\nCiao! Thank you for using CLI Toolbox.")
            break

        else:
            print("\nInvalid option. Please try again.")
            input("Press Enter to continue...")


if __name__ == "__main__":
    main()