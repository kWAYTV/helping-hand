"""Utility helper functions"""

import os
import platform
import secrets
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
    """Add a humanized delay between actions using secure randomization"""
    # Ensure valid range
    if min_seconds > max_seconds:
        min_seconds, max_seconds = max_seconds, min_seconds

    # Use cryptographically secure randomization for better human simulation
    # Generate a random float between 0 and 1 using secure random bytes
    random_bytes = secrets.randbits(32)  # 32-bit random number
    random_float = random_bytes / (2**32)  # Convert to 0.0-1.0 range

    # Apply to our delay range
    delay = min_seconds + (random_float * (max_seconds - min_seconds))

    logger.debug(f"Humanized delay for {action}: {delay:.2f}s")
    sleep(delay)


def humanized_delay_from_config(
    config_manager, delay_type: str = "general", action: str = "action"
) -> None:
    """Add a humanized delay using config values"""
    if delay_type == "moving":
        min_delay, max_delay = config_manager.get_moving_delays()
    elif delay_type == "thinking":
        min_delay, max_delay = config_manager.get_thinking_delays()
    else:  # general
        min_delay, max_delay = config_manager.get_general_delays()

    humanized_delay(min_delay, max_delay, action)


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
