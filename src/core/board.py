"""Board Handler - Chess board interaction and move detection"""

import re
from math import ceil
from time import sleep
from typing import List, Optional

import chess
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from ..core.browser import BrowserManager
from ..utils.debug import DebugUtils
from ..utils.helpers import advanced_humanized_delay, humanized_delay
from ..utils.resilience import element_retry, move_retry, safe_execute


class BoardHandler:
    """Handles chess board interactions and move detection"""

    def __init__(
        self,
        browser_manager: BrowserManager,
        debug_utils: DebugUtils,
        config_manager=None,
    ):
        self.browser_manager = browser_manager
        self.debug_utils = debug_utils
        self.driver = browser_manager.get_driver()
        self.config_manager = config_manager

    def wait_for_game_ready(self) -> bool:
        """Wait for game to be ready and return True if successful"""
        logger.debug("Waiting for game setup")

        # Wait for follow-up to disappear
        while self.browser_manager.check_exists_by_class("follow-up"):
            logger.debug("Found follow-up element, waiting for user action...")
            sleep(1)

        logger.debug("No follow-up found, waiting for game interface")

        try:
            # Wait for board first (this appears quickly)
            WebDriverWait(self.driver, 30).until(
                ec.presence_of_element_located((By.CLASS_NAME, "cg-wrap"))
            )
            logger.debug("Board found")

            # Try multiple selectors for move input box (more flexible)
            move_input_selectors = [
                (By.CLASS_NAME, "ready"),  # Most common selector
                (By.XPATH, "/html/body/div[2]/main/div[1]/div[10]/input"),  # Original
                (By.CSS_SELECTOR, "input[placeholder*='move']"),  # CSS alternative
                (By.CSS_SELECTOR, ".move-input"),  # Class alternative
                (By.TAG_NAME, "input"),  # Last resort - any input
            ]

            move_input_found = False
            for selector_type, selector_value in move_input_selectors:
                try:
                    WebDriverWait(self.driver, 5).until(
                        ec.presence_of_element_located((selector_type, selector_value))
                    )
                    logger.debug(
                        f"Move input found using {selector_type}: {selector_value}"
                    )
                    move_input_found = True
                    break
                except:
                    continue

            if not move_input_found:
                # Try a longer wait for the most reliable selector
                logger.debug("Trying longer wait for move input...")
                WebDriverWait(self.driver, 30).until(
                    ec.presence_of_element_located((By.CLASS_NAME, "ready"))
                )
                logger.debug("Move input found after extended wait")

            logger.debug("Game interface ready")
            return True

        except Exception as e:
            logger.error(f"Failed to wait for game ready: {e}")
            return False

    def determine_player_color(self) -> str:
        """Determine if we're playing as White or Black"""
        board_set_for_white = self.browser_manager.check_exists_by_class(
            "orientation-white"
        )

        if board_set_for_white:
            logger.info("Playing as WHITE")
            return "W"
        else:
            logger.info("Playing as BLACK")
            return "B"

    @element_retry(max_retries=3, delay=1.0)
    def get_move_input_handle(self):
        """Get the move input element"""
        # Try multiple selectors for better reliability
        move_input_selectors = [
            (By.CLASS_NAME, "ready"),  # Most common selector
            (By.XPATH, "/html/body/div[2]/main/div[1]/div[10]/input"),  # Original
            (By.CSS_SELECTOR, "input[placeholder*='move']"),  # CSS alternative
            (By.CSS_SELECTOR, ".move-input"),  # Class alternative
        ]

        for selector_type, selector_value in move_input_selectors:
            try:
                WebDriverWait(self.driver, 10).until(
                    ec.presence_of_element_located((selector_type, selector_value))
                )
                element = self.driver.find_element(selector_type, selector_value)
                logger.debug(
                    f"Move input handle found using {selector_type}: {selector_value}"
                )
                return element
            except Exception:
                continue

        # If all specific selectors fail, try the fallback
        try:
            WebDriverWait(self.driver, 5).until(
                ec.presence_of_element_located((By.TAG_NAME, "input"))
            )
            elements = self.driver.find_elements(By.TAG_NAME, "input")
            # Return the first visible input element
            for element in elements:
                if element.is_displayed():
                    logger.debug(
                        "Move input handle found using fallback input selector"
                    )
                    return element
        except Exception as e:
            logger.error(f"Failed to find move input handle: {e}")
            return None

        logger.error("Could not find move input handle with any selector")
        return None

    @move_retry(max_retries=3, delay=0.5)
    def find_move_by_alternatives(self, move_number: int):
        """Try alternative selectors to find moves"""
        # Try finding all moves and get by index (most reliable)
        try:
            elements = self.driver.find_elements(By.CLASS_NAME, "kwdb")
            if len(elements) >= move_number:
                element = elements[move_number - 1]  # 0-based indexing
                move_text = element.text.strip()
                if move_text:  # Only return if there's actual text
                    logger.debug(
                        f"Found move {move_number}: '{move_text}' by class index"
                    )
                    return element
        except:
            pass

        # Alternative selectors to try (only if class method fails)
        selectors = [
            f"//kwdb[{move_number}]",  # Shortest XPath
            f"//rm6/l4x/kwdb[{move_number}]",  # Medium XPath
            f"/html/body/div[2]/main/div[1]/rm6/l4x/kwdb[{move_number}]",  # Original
        ]

        for selector in selectors:
            try:
                element = self.driver.find_element(By.XPATH, selector)
                move_text = element.text.strip()
                if move_text:  # Only return if there's actual text
                    logger.debug(
                        f"Found move {move_number}: '{move_text}' using {selector}"
                    )
                    return element
            except:
                continue

        return None

    def get_previous_moves(self, board: chess.Board) -> int:
        """Get all previous moves and update board, return current move number"""
        logger.debug("Getting previous moves from board")
        temp_move_number = 1

        # First check if there are ANY moves at all
        first_move = self.find_move_by_alternatives(1)
        if not first_move:
            logger.debug(
                "No moves found on board - this appears to be the start of the game"
            )
            return 1  # Start from move 1

        while temp_move_number < 999:  # Safety limit
            move_element = self.find_move_by_alternatives(temp_move_number)

            if move_element:
                move_text = move_element.text.strip()
                if (
                    not move_text or move_text == "..."
                ):  # Skip empty or placeholder moves
                    temp_move_number += 1
                    continue

                logger.debug(f"Found previous move {temp_move_number}: {move_text}")
                try:
                    board.push_san(move_text)
                    temp_move_number += 1
                except Exception as e:
                    logger.error(f"Invalid move notation '{move_text}': {e}")
                    self.debug_utils.save_debug_info(
                        self.driver, temp_move_number, board
                    )
                    break
            else:
                logger.debug(
                    f"No more previous moves found. Total moves processed: {temp_move_number - 1}"
                )
                # Only save debug info if we have moves but can't parse them
                if temp_move_number == 1:
                    logger.debug("No moves on board - starting fresh game")
                elif (
                    temp_move_number <= 3
                ):  # If we can't find early moves (might be selector issue)
                    logger.warning(
                        "Could not find expected moves, investigating selectors"
                    )
                    self.debug_utils.debug_move_list_structure(self.driver)
                    self.debug_utils.save_debug_info(
                        self.driver, temp_move_number, board
                    )
                break

        return temp_move_number

    def check_for_move(self, move_number: int) -> Optional[str]:
        """Check if a move exists at the given position and return move text"""
        move_element = self.find_move_by_alternatives(move_number)

        if move_element:
            move_text = move_element.text.strip()
            if move_text and move_text != "...":  # Exclude empty and placeholder moves
                return move_text

        return None

    def validate_and_push_move(
        self,
        board: chess.Board,
        move_text: str,
        move_number: int,
        is_our_move: bool = False,
    ) -> bool:
        """Validate and push a move to the board"""
        try:
            # Check if move is legal in current position
            test_move = board.parse_san(move_text)
            if test_move in board.legal_moves:
                uci = board.push_san(move_text)
                move_desc = "us" if is_our_move else "opponent"
                logger.success(f"{ceil(move_number / 2)}. {uci.uci()} [{move_desc}]")
                return True
            else:
                logger.warning(f"Move '{move_text}' is not legal in current position")
                self.debug_utils.save_debug_info(self.driver, move_number, board)
                return False
        except Exception as e:
            logger.error(f"Invalid move notation '{move_text}': {e}")
            self.debug_utils.save_debug_info(self.driver, move_number, board)
            return False

    @move_retry(max_retries=3, delay=1.0)
    def execute_move(self, move: chess.Move, move_number: int) -> None:
        """Execute a move through the interface"""
        logger.debug(f"Executing move: {move}")

        # Advanced humanized delay before making the move
        if self.config_manager:
            advanced_humanized_delay("move execution", self.config_manager, "moving")
        else:
            humanized_delay(0.5, 1.5, "move execution")

        self.clear_arrow()

        # Get fresh move handle to avoid stale element reference
        move_handle = self.get_move_input_handle()
        if not move_handle:
            logger.error("Failed to get fresh move input handle")
            raise Exception("Could not find move input handle")

        # Advanced humanized typing delay
        if self.config_manager:
            advanced_humanized_delay("move input", self.config_manager, "base")
        else:
            humanized_delay(0.3, 0.8, "move input")

        # Execute move input with safe execution
        def _send_move_input():
            move_handle.send_keys(Keys.RETURN)
            move_handle.clear()

            # Type move with slight delay and additional jitter
            if self.config_manager:
                advanced_humanized_delay("typing move", self.config_manager, "base")
            else:
                humanized_delay(0.2, 0.5, "typing move")

            move_handle.send_keys(str(move))

        safe_execute(_send_move_input, log_errors=True)

    def clear_arrow(self) -> None:
        """Clear any arrows on the board"""
        self.browser_manager.execute_script(
            """
            var g = document.getElementsByTagName("g")[0];
            if (g) {
                g.textContent = "";
            }
            """
        )

    def draw_arrow(self, move: chess.Move, our_color: str) -> None:
        """Draw an arrow showing the suggested move"""
        move_str = str(move)
        src_square = move_str[:2]
        dst_square = move_str[2:]
        logger.debug(
            f"Drawing move arrow: {src_square} → {dst_square} (green circle = source, gold circle = destination)"
        )

        transform = self._get_piece_transform(move, our_color)

        move_str = str(move)
        src = str(move_str[:2])
        dst = str(move_str[2:])

        board_style = self.driver.find_element(
            By.XPATH, "/html/body/div[2]/main/div[1]/div[1]/div/cg-container"
        ).get_attribute("style")
        board_size = re.search(r"\d+", board_style).group()

        self.browser_manager.execute_script(
            """
            var x1 = arguments[0];
            var y1 = arguments[1];
            var x2 = arguments[2];
            var y2 = arguments[3];
            var size = arguments[4];
            var src = arguments[5];
            var dst = arguments[6];

            defs = document.getElementsByTagName("defs")[0];
            child_defs = document.getElementsByTagName("marker")[0];

            if (child_defs == null) {
                child_defs = document.createElementNS("http://www.w3.org/2000/svg", "marker");
                child_defs.setAttribute("id", "arrowhead-g");
                child_defs.setAttribute("orient", "auto");
                child_defs.setAttribute("markerWidth", "4");
                child_defs.setAttribute("markerHeight", "8");
                child_defs.setAttribute("refX", "2.05");
                child_defs.setAttribute("refY", "2.01");
                child_defs.setAttribute("cgKey", "g");
                
                path = document.createElement('path')
                path.setAttribute("d", "M0,0 V4 L3,2 Z");
                path.setAttribute("fill", "#15781B");
                child_defs.appendChild(path);
                defs.appendChild(child_defs);
            }

            g = document.getElementsByTagName("g")[0];
            
            // Create the main arrow line
            var child_g = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            child_g.setAttribute("stroke","#15781B");
            child_g.setAttribute("stroke-width","0.15625");
            child_g.setAttribute("stroke-linecap","round");
            child_g.setAttribute("marker-end","url(#arrowhead-g)");
            child_g.setAttribute("opacity","1");
            child_g.setAttribute("x1", x1);
            child_g.setAttribute("y1", y1);
            child_g.setAttribute("x2", x2);
            child_g.setAttribute("y2", y2);
            child_g.setAttribute("cgHash", `${size}, ${size},` + src + `,` + dst + `,green`);
            g.appendChild(child_g);
            
            // Add subtle destination indicator (small dot)
            var destIndicator = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            destIndicator.setAttribute("cx", x2);
            destIndicator.setAttribute("cy", y2);
            destIndicator.setAttribute("r", "0.08");
            destIndicator.setAttribute("fill", "#FFD700");
            destIndicator.setAttribute("fill-opacity", "0.9");
            destIndicator.setAttribute("stroke", "#15781B");
            destIndicator.setAttribute("stroke-width", "0.02");
            destIndicator.setAttribute("cgHash", `${size}, ${size},` + src + `,` + dst + `,destination`);
            g.appendChild(destIndicator);
            
            // Add very subtle pulsing to destination
            var pulseAnim = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
            pulseAnim.setAttribute("attributeName", "r");
            pulseAnim.setAttribute("values", "0.08;0.12;0.08");
            pulseAnim.setAttribute("dur", "2s");
            pulseAnim.setAttribute("repeatCount", "indefinite");
            destIndicator.appendChild(pulseAnim);
            """,
            transform[0],
            transform[1],
            transform[2],
            transform[3],
            board_size,
            src,
            dst,
        )

    def _get_piece_transform(self, move: chess.Move, our_color: str) -> List[float]:
        """Calculate arrow coordinates for the move"""
        rank_values_w = [
            ("a", -3.5),
            ("b", -2.5),
            ("c", -1.5),
            ("d", -0.5),
            ("e", 0.5),
            ("f", 1.5),
            ("g", 2.5),
            ("h", 3.5),
        ]
        file_values_w = [
            (1, 3.5),
            (2, 2.5),
            (3, 1.5),
            (4, 0.5),
            (5, -0.5),
            (6, -1.5),
            (7, -2.5),
            (8, -3.5),
        ]

        rank_values_b = [
            ("a", 3.5),
            ("b", 2.5),
            ("c", 1.5),
            ("d", 0.5),
            ("e", -0.5),
            ("f", -1.5),
            ("g", -2.5),
            ("h", -3.5),
        ]
        file_values_b = [
            (1, -3.5),
            (2, -2.5),
            (3, -1.5),
            (4, -0.5),
            (5, 0.5),
            (6, 1.5),
            (7, 2.5),
            (8, 3.5),
        ]

        move_str = str(move)
        _from = str(move_str[:2])
        _to = str(move_str[2:])

        # Get source coordinates
        for i, (rank, value) in enumerate(
            rank_values_w if our_color == "W" else rank_values_b
        ):
            if rank == _from[0]:
                src_x = value
                break

        for i, (file, value) in enumerate(
            file_values_w if our_color == "W" else file_values_b
        ):
            if file == int(_from[1]):
                src_y = value
                break

        # Get destination coordinates
        for i, (rank, value) in enumerate(
            rank_values_w if our_color == "W" else rank_values_b
        ):
            if rank == _to[0]:
                dst_x = value
                break

        for i, (file, value) in enumerate(
            file_values_w if our_color == "W" else file_values_b
        ):
            if file == int(_to[1]):
                dst_y = value
                break

        return [src_x, src_y, dst_x, dst_y]

    def is_game_over(self) -> bool:
        """Check if game is over (follow-up element exists)"""
        return bool(
            safe_execute(
                self.browser_manager.check_exists_by_class,
                "follow-up",
                default_return=False,
                log_errors=False,
            )
        )
