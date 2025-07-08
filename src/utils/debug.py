"""Debug utilities for troubleshooting"""

import glob
import os
import time
from typing import Optional

import chess
from loguru import logger


class DebugUtils:
    """Utilities for debugging and troubleshooting"""

    def __init__(self, debug_dir: str = "debug"):
        self.debug_dir = debug_dir
        self.setup_debug_folder()

    def setup_debug_folder(self) -> None:
        """Create debug folder and clean up old files"""
        # Create debug folder if it doesn't exist
        if not os.path.exists(self.debug_dir):
            os.makedirs(self.debug_dir)
            logger.debug(f"Created debug folder: {self.debug_dir}")

        # Clean up old debug files
        try:
            debug_files = glob.glob(os.path.join(self.debug_dir, "*"))
            if debug_files:
                for file_path in debug_files:
                    os.remove(file_path)
                logger.debug(f"Cleaned up {len(debug_files)} old debug files")
            else:
                logger.debug("No old debug files to clean up")
        except Exception as e:
            logger.warning(f"Failed to clean up debug files: {e}")

    def save_debug_info(
        self, driver, move_number: int, board: Optional[chess.Board] = None
    ) -> None:
        """Save debugging information when stuck"""
        try:
            timestamp = int(time.time())

            # Save screenshot
            screenshot_path = os.path.join(
                self.debug_dir, f"screenshot_move{move_number}_{timestamp}.png"
            )
            driver.save_screenshot(screenshot_path)
            logger.debug(f"Saved screenshot to {screenshot_path}")

            # Save page source
            html_path = os.path.join(
                self.debug_dir, f"page_move{move_number}_{timestamp}.html"
            )
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            logger.debug(f"Saved page HTML to {html_path}")

            # Save board state if available
            if board:
                board_path = os.path.join(
                    self.debug_dir, f"board_move{move_number}_{timestamp}.txt"
                )
                with open(board_path, "w") as f:
                    f.write(f"Current board FEN: {board.fen()}\n")
                    f.write(f"Board state:\n{board}\n")
                    f.write(
                        f"Legal moves: {[str(move) for move in board.legal_moves]}\n"
                    )
                    f.write(f"Turn: {'White' if board.turn else 'Black'}\n")
                    f.write(f"Move number: {move_number}\n")
                logger.debug(f"Saved board state to {board_path}")

            # Log current URL
            logger.debug(f"Current URL: {driver.current_url}")

        except Exception as e:
            logger.error(f"Failed to save debug info: {e}")

    def debug_move_list_structure(self, driver) -> None:
        """Debug function to inspect the actual HTML structure of moves"""
        logger.info("=== DEBUGGING MOVE LIST STRUCTURE ===")

        # Try different possible selectors (modern first, then legacy)
        selectors_to_try = [
            # Modern selectors
            ".moves .move",
            ".move-list .move",
            ".game-moves .move",
            "[data-testid*='move']",
            ".moves span",
            ".move",
            ".pgn .move",
            "moveOn",
            "move",
            # Legacy selectors
            "kwdb",
            "rm6",
            "l4x",
            "san",
        ]

        for selector in selectors_to_try:
            try:
                from selenium.webdriver.common.by import By

                if selector.startswith("."):
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                elif selector.startswith("["):
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                else:
                    elements = driver.find_elements(By.CLASS_NAME, selector)

                logger.info(f"Selector '{selector}': Found {len(elements)} elements")
                for i, elem in enumerate(elements[:5]):  # Show first 5
                    try:
                        text = elem.text.strip()
                        tag = elem.tag_name
                        classes = elem.get_attribute("class")
                        logger.info(
                            f"  [{i}] Tag: {tag}, Classes: {classes}, Text: '{text}'"
                        )
                    except:
                        logger.debug(f"  [{i}] Could not get element info")
            except Exception as e:
                logger.debug(f"Selector '{selector}' failed: {e}")

        # Try to find the move list container
        try:
            page_source = driver.page_source
            import re

            # Look for move-related patterns in HTML (modern and legacy)
            patterns = [
                "move",
                "moves",
                "move-list",
                "pgn",
                "kwdb",
                "l4x",
                "rm6",
                "san",
                "moveOn",
            ]
            for pattern in patterns:
                matches = re.findall(f".*{pattern}.*", page_source, re.IGNORECASE)
                if matches:
                    logger.info(f"Pattern '{pattern}' found in HTML:")
                    for match in matches[:3]:  # Show first 3 matches
                        logger.info(f"  {match[:200]}")  # Truncate long lines
        except Exception as e:
            logger.error(f"Could not analyze page source: {e}")
