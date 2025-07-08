"""Board Handler - Chess board interaction and move detection"""

import re
from math import ceil
from time import sleep
from typing import List, Optional, Tuple

import chess
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from ..core.browser import BrowserManager
from ..utils.debug import DebugUtils
from ..utils.helpers import humanized_delay_from_config


class BoardHandler:
    """Handles chess board interactions and move detection"""

    def __init__(self, browser_manager: BrowserManager, debug_utils: DebugUtils):
        self.browser_manager = browser_manager
        self.debug_utils = debug_utils
        self.driver = browser_manager.get_driver()

    def wait_for_game_ready(self) -> bool:
        """Wait for game to be ready and return True if successful"""
        logger.info("Waiting for game setup")
        follow_up_wait_count = 0
        game_result_logged = False

        # Wait for follow-up to disappear
        while self.browser_manager.check_exists_by_class("follow-up"):
            follow_up_wait_count += 1

            # Log game result once when first detected
            if not game_result_logged:
                self._log_game_result()
                game_result_logged = True

            # Reduce spam by logging every 10 seconds instead of every second
            if follow_up_wait_count % 10 == 0:
                logger.debug(
                    f"Still waiting for follow-up to clear... ({follow_up_wait_count}s)"
                )

            sleep(1)

        logger.info("No follow-up found, waiting for user to start game")

        try:
            # Wait for move input box
            WebDriverWait(self.driver, 600).until(
                ec.presence_of_element_located(
                    (By.XPATH, "/html/body/div[2]/main/div[1]/div[10]/input")
                )
            )
            logger.info("Move input box found")

            # Wait for board
            WebDriverWait(self.driver, 600).until(
                ec.presence_of_element_located((By.CLASS_NAME, "cg-wrap"))
            )
            logger.info("Board found")

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

    def get_move_input_handle(self):
        """Get the move input element"""
        try:
            WebDriverWait(self.driver, 600).until(
                ec.presence_of_element_located((By.CLASS_NAME, "ready"))
            )
            return self.driver.find_element(By.CLASS_NAME, "ready")
        except Exception as e:
            logger.error(f"Failed to find move input handle: {e}")
            return None

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
        logger.info("Getting previous moves from board")
        temp_move_number = 1

        while temp_move_number < 999:  # Safety limit
            move_xpath = (
                f"/html/body/div[2]/main/div[1]/rm6/l4x/kwdb[{temp_move_number}]"
            )
            move_element = self.browser_manager.check_exists_by_xpath(move_xpath)

            if not move_element:
                move_element = self.find_move_by_alternatives(temp_move_number)

            if move_element:
                move_text = move_element.text.strip()
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
                logger.info(
                    f"No more previous moves found. Total moves processed: {temp_move_number - 1}"
                )
                # Save debug info if we expected more moves but couldn't find them
                if temp_move_number <= 3:  # If we can't even find the first few moves
                    logger.warning("Could not find expected moves, saving debug info")
                    self.debug_utils.debug_move_list_structure(self.driver)
                    self.debug_utils.save_debug_info(
                        self.driver, temp_move_number, board
                    )
                break

        return temp_move_number

    def check_for_move(self, move_number: int) -> Optional[str]:
        """Check if a move exists at the given position and return move text"""
        move_xpath = f"/html/body/div[2]/main/div[1]/rm6/l4x/kwdb[{move_number}]"
        move_element = self.browser_manager.check_exists_by_xpath(move_xpath)

        if not move_element:
            move_element = self.find_move_by_alternatives(move_number)

        if move_element:
            return move_element.text.strip()

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
                logger.info(f"Move {ceil(move_number / 2)}: {uci.uci()} [{move_desc}]")
                return True
            else:
                logger.warning(f"Move '{move_text}' is not legal in current position")
                self.debug_utils.save_debug_info(self.driver, move_number, board)
                return False
        except Exception as e:
            logger.error(f"Invalid move notation '{move_text}': {e}")
            self.debug_utils.save_debug_info(self.driver, move_number, board)
            return False

    def execute_move(
        self, move: chess.Move, move_handle, move_number: int, config_manager
    ) -> None:
        """Execute a move through the interface"""
        logger.info(f"Executing move: {move}")

        # Humanized delay before making the move (keep arrow visible)
        humanized_delay_from_config(config_manager, "moving", "move execution")

        logger.info(f"Move {ceil(move_number / 2)}: {move} [us]")

        # Humanized typing delay (keep arrow visible)
        humanized_delay_from_config(config_manager, "general", "move input")
        move_handle.send_keys(Keys.RETURN)
        move_handle.clear()

        # Type move with slight delay (keep arrow visible)
        humanized_delay_from_config(config_manager, "general", "typing move")
        move_handle.send_keys(str(move))

        # Clear arrow only after move is completely executed
        self.clear_arrow()

    def clear_arrow(self) -> None:
        """Clear any arrows on the board"""
        self.browser_manager.execute_script(
            """
            g = document.getElementsByTagName("g")[0];
            g.textContent = "";
            """
        )

    def draw_arrow(self, move: chess.Move, our_color: str) -> None:
        """Draw an arrow showing the suggested move"""
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

            if (child_defs == null)
            {
                child_defs = document.createElementNS("http://www.w3.org/2000/svg", "marker");
                child_defs.setAttribute("id", "arrowhead-custom");
                child_defs.setAttribute("orient", "auto");
                child_defs.setAttribute("markerWidth", "6");
                child_defs.setAttribute("markerHeight", "10");
                child_defs.setAttribute("refX", "3");
                child_defs.setAttribute("refY", "3");
                child_defs.setAttribute("cgKey", "custom");

                path = document.createElement('path')
                path.setAttribute("d", "M0,0 V6 L4,3 Z");
                path.setAttribute("fill", "#4CAF50");
                path.setAttribute("stroke", "#2E7D32");
                path.setAttribute("stroke-width", "0.3");
                child_defs.appendChild(path);

                defs.appendChild(child_defs);
            }

            g = document.getElementsByTagName("g")[0];

            var child_g = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            child_g.setAttribute("stroke", "#4CAF50");
            child_g.setAttribute("stroke-width", "0.25");
            child_g.setAttribute("stroke-linecap", "round");
            child_g.setAttribute("marker-end", "url(#arrowhead-custom)");
            child_g.setAttribute("opacity", "0.95");
            child_g.setAttribute("x1", x1);
            child_g.setAttribute("y1", y1);
            child_g.setAttribute("x2", x2);
            child_g.setAttribute("y2", y2);
            child_g.setAttribute("cgHash", `${size}, ${size},` + src + `,` + dst + `,custom`);

            g.appendChild(child_g);
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
        return bool(self.browser_manager.check_exists_by_class("follow-up"))

    def _log_game_result(self) -> None:
        """Log the game result when game ends"""
        try:
            # Get score using driver directly
            score_element = self.driver.find_element(
                By.XPATH, "/html/body/div[2]/main/div[1]/rm6/l4x/div/p[1]"
            )
            score = score_element.text if score_element else "Score not found"

            # Get result reason using driver directly
            result_element = self.driver.find_element(
                By.XPATH, "/html/body/div[2]/main/div[1]/rm6/l4x/div/p[2]"
            )
            result = result_element.text if result_element else "Result not found"

            logger.success(f"🏁 GAME FINISHED - {score} | {result}")
            logger.success(f"📊 Final Score: {score}")
            logger.success(f"🎯 Game Result: {result}")

        except Exception as e:
            logger.debug(f"Could not extract game result: {e}")
            logger.info("🏁 GAME FINISHED - Result details not available")
