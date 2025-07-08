"""Utility helper functions"""

import os
import platform
import random
import time
from time import sleep

from loguru import logger


def get_geckodriver_path() -> str:
    """Get the correct geckodriver path for current OS"""
    system = platform.system().lower()
    if system == "windows":
        return os.path.join("deps", "geckodriver", "geckodriver.exe")
    else:
        return os.path.join("deps", "geckodriver", "geckodriver")


def get_stockfish_path() -> str:
    """Get the correct Stockfish path for current OS"""
    system = platform.system().lower()
    if system == "windows":
        return os.path.join("deps", "stockfish", "stockfish.exe")
    else:
        return os.path.join("deps", "stockfish", "stockfish")


def humanized_delay(
    min_seconds: float = 0.5, max_seconds: float = 2.0, action: str = "action"
) -> None:
    """Add a humanized delay between actions"""
    delay = random.uniform(min_seconds, max_seconds)
    logger.debug(f"Humanized delay for {action}: {delay:.2f}s")
    sleep(delay)


def clear_screen() -> None:
    """Clear the terminal screen on both Windows and Unix-like systems"""
    os.system("cls" if os.name == "nt" else "clear")


def get_seconds(time_str: str) -> int:
    """Convert time string to seconds"""
    semicolons = time_str.count(":")

    if semicolons == 2:
        # hh, mm, ss
        hh, mm, ss = time_str.split(":")
        return int(hh) * 3600 + int(mm) * 60 + int(ss)
    elif semicolons == 1:
        fixed = time_str.partition(".")
        # mm, ss
        mm, ss = fixed[0].split(":")
        return int(mm) * 60 + int(ss)

    return 0
