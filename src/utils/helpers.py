"""Utility helper functions"""

import os
import platform
import random
import sys
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


def get_xpath_finder_path() -> str:
    """Get the xpath_finder extension path"""
    return os.path.join("deps", "xpath_finder.xpi")


def install_firefox_extensions(driver):
    """Install Firefox extensions after browser startup"""
    from loguru import logger

    extension_path = get_xpath_finder_path()
    if os.path.exists(extension_path):
        try:
            driver.install_addon(extension_path)
            logger.debug(f"Successfully installed extension: {extension_path}")
        except Exception as e:
            logger.warning(f"Failed to install extension {extension_path}: {e}")


def humanized_delay(
    min_seconds: float = 0.5,
    max_seconds: float = 2.0,
    action: str = "action",
    config_manager=None,
    delay_type: str = "base",
) -> None:
    """Add a humanized delay between actions with advanced jitter"""
    # Use config if provided, otherwise use parameters
    if config_manager:
        try:
            min_seconds, max_seconds = config_manager.get_humanization_delay(delay_type)
        except:
            # Fallback to provided parameters
            pass

    # Base delay from config
    base_delay = random.uniform(min_seconds, max_seconds)

    # Add jitter (0-1 seconds additional randomness)
    jitter = random.uniform(0, 1.0)

    # Micro-variations to make it more human-like
    micro_variation = random.uniform(-0.1, 0.1)

    # Final delay with all variations
    final_delay = base_delay + jitter + micro_variation

    # Ensure minimum delay of 0.1s
    final_delay = max(0.1, final_delay)

    logger.debug(f"Delaying {action} for {final_delay:.2f}s")

    sleep(final_delay)


def advanced_humanized_delay(
    action: str = "action", config_manager=None, delay_type: str = "base"
) -> None:
    """Advanced humanized delay using only config manager"""
    if not config_manager:
        # Fallback to basic delay
        humanized_delay(0.5, 2.0, action)
        return

    min_seconds, max_seconds = config_manager.get_humanization_delay(delay_type)

    # Advanced human-like patterns
    base_delay = random.uniform(min_seconds, max_seconds)

    # Add multiple layers of randomness
    jitter_1 = random.uniform(0, 0.8)  # Primary jitter
    jitter_2 = random.uniform(0, 0.3)  # Secondary jitter

    # Occasional longer pauses (10% chance)
    if random.random() < 0.1:
        pause_bonus = random.uniform(0.5, 1.5)
        logger.debug(f"Adding thinking pause: {pause_bonus:.2f}s")
    else:
        pause_bonus = 0

    # Micro-hesitations
    micro_hesitation = random.uniform(-0.05, 0.15)

    # Final calculation
    final_delay = base_delay + jitter_1 + jitter_2 + pause_bonus + micro_hesitation
    final_delay = max(0.1, final_delay)

    logger.debug(f"Delaying {action} (advanced) for {final_delay:.2f}s")

    sleep(final_delay)


def clear_screen() -> None:
    """Clear the terminal screen on both Windows and Unix-like systems"""
    os.system("cls" if os.name == "nt" else "clear")


def signal_handler(sig, frame):
    """Handle graceful shutdown"""
    logger.info("Received interrupt signal, shutting down...")
    sys.exit(0)


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
