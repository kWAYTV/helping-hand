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
from ..utils.helpers import advanced_humanized_delay, humanized_delay


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
        logger.info("Waiting for game setup")

        # Wait for follow-up to disappear
        while self.browser_manager.check_exists_by_class("follow-up"):
            logger.debug("Found follow-up element, waiting...")
            sleep(1)

        logger.info("No follow-up found, waiting for user's first move")

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
                print(f"{ceil(move_number / 2)}. {uci.uci()} [{move_desc}]")
                return True
            else:
                logger.warning(f"Move '{move_text}' is not legal in current position")
                self.debug_utils.save_debug_info(self.driver, move_number, board)
                return False
        except Exception as e:
            logger.error(f"Invalid move notation '{move_text}': {e}")
            self.debug_utils.save_debug_info(self.driver, move_number, board)
            return False

    def execute_move(self, move: chess.Move, move_handle, move_number: int) -> None:
        """Execute a move through the interface"""
        logger.info(f"Executing move: {move}")

        # Advanced humanized delay before making the move
        if self.config_manager:
            advanced_humanized_delay("move execution", self.config_manager, "moving")
        else:
            humanized_delay(0.5, 1.5, "move execution")

        self.clear_arrow()

        logger.info(f"Move {ceil(move_number / 2)}: {move} [us]")
        print(f"{ceil(move_number / 2)}. {move} [us]")

        # Advanced humanized typing delay
        if self.config_manager:
            advanced_humanized_delay("move input", self.config_manager, "base")
        else:
            humanized_delay(0.3, 0.8, "move input")

        move_handle.send_keys(Keys.RETURN)
        move_handle.clear()

        # Type move with slight delay and additional jitter
        if self.config_manager:
            advanced_humanized_delay("typing move", self.config_manager, "base")
        else:
            humanized_delay(0.2, 0.5, "typing move")

        move_handle.send_keys(str(move))

    def clear_arrow(self) -> None:
        """Clear any arrows and highlights on the board"""
        self.browser_manager.execute_script(
            """
            var g = document.getElementsByTagName("g")[0];
            if (g) {
                // Remove only our enhanced arrows and highlights
                var enhancedElements = g.querySelectorAll('[data-arrow="enhanced"]');
                enhancedElements.forEach(function(element) {
                    element.remove();
                });
                
                // Also clear any legacy arrows (backward compatibility)
                var legacyArrows = g.querySelectorAll('line[cgHash*="green"]');
                legacyArrows.forEach(function(arrow) {
                    arrow.remove();
                });
                
                // Clear any highlight circles
                var highlights = g.querySelectorAll('[data-highlight]');
                highlights.forEach(function(highlight) {
                    highlight.remove();
                });
            }
            """
        )

    def draw_arrow(self, move: chess.Move, our_color: str) -> None:
        """Draw an enhanced arrow showing the suggested move"""
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

            // Get or create the defs element
            var defs = document.getElementsByTagName("defs")[0];
            if (!defs) {
                defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
                document.getElementsByTagName("svg")[0].appendChild(defs);
            }

            // Create enhanced arrowhead with glow effect
            var arrowId = "enhanced-arrowhead";
            var existingArrow = document.getElementById(arrowId);
            if (!existingArrow) {
                // Create gradient for the arrow
                var gradient = document.createElementNS("http://www.w3.org/2000/svg", "linearGradient");
                gradient.setAttribute("id", "arrow-gradient");
                gradient.setAttribute("x1", "0%");
                gradient.setAttribute("y1", "0%");
                gradient.setAttribute("x2", "100%");
                gradient.setAttribute("y2", "0%");
                
                var stop1 = document.createElementNS("http://www.w3.org/2000/svg", "stop");
                stop1.setAttribute("offset", "0%");
                stop1.setAttribute("stop-color", "#00ff88");
                stop1.setAttribute("stop-opacity", "1");
                
                var stop2 = document.createElementNS("http://www.w3.org/2000/svg", "stop");
                stop2.setAttribute("offset", "100%");
                stop2.setAttribute("stop-color", "#00cc66");
                stop2.setAttribute("stop-opacity", "1");
                
                gradient.appendChild(stop1);
                gradient.appendChild(stop2);
                defs.appendChild(gradient);

                // Create glow filter
                var filter = document.createElementNS("http://www.w3.org/2000/svg", "filter");
                filter.setAttribute("id", "arrow-glow");
                filter.setAttribute("x", "-50%");
                filter.setAttribute("y", "-50%");
                filter.setAttribute("width", "200%");
                filter.setAttribute("height", "200%");
                
                var feGaussianBlur = document.createElementNS("http://www.w3.org/2000/svg", "feGaussianBlur");
                feGaussianBlur.setAttribute("stdDeviation", "3");
                feGaussianBlur.setAttribute("result", "coloredBlur");
                
                var feMerge = document.createElementNS("http://www.w3.org/2000/svg", "feMerge");
                var feMergeNode1 = document.createElementNS("http://www.w3.org/2000/svg", "feMergeNode");
                feMergeNode1.setAttribute("in", "coloredBlur");
                var feMergeNode2 = document.createElementNS("http://www.w3.org/2000/svg", "feMergeNode");
                feMergeNode2.setAttribute("in", "SourceGraphic");
                
                feMerge.appendChild(feMergeNode1);
                feMerge.appendChild(feMergeNode2);
                filter.appendChild(feGaussianBlur);
                filter.appendChild(feMerge);
                defs.appendChild(filter);

                // Create enhanced arrowhead
                var marker = document.createElementNS("http://www.w3.org/2000/svg", "marker");
                marker.setAttribute("id", arrowId);
                marker.setAttribute("orient", "auto");
                marker.setAttribute("markerWidth", "8");
                marker.setAttribute("markerHeight", "10");
                marker.setAttribute("refX", "7");
                marker.setAttribute("refY", "3");
                
                var arrowPath = document.createElementNS("http://www.w3.org/2000/svg", "path");
                arrowPath.setAttribute("d", "M0,0 L0,6 L7,3 z");
                arrowPath.setAttribute("fill", "url(#arrow-gradient)");
                arrowPath.setAttribute("stroke", "#00ff88");
                arrowPath.setAttribute("stroke-width", "0.5");
                arrowPath.setAttribute("filter", "url(#arrow-glow)");
                
                marker.appendChild(arrowPath);
                defs.appendChild(marker);
            }

            // Clear previous arrows
            var g = document.getElementsByTagName("g")[0];
            var existingArrows = g.querySelectorAll('[data-arrow="enhanced"]');
            existingArrows.forEach(function(arrow) {
                arrow.remove();
            });

            // Create enhanced arrow line with animation
            var arrowLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            arrowLine.setAttribute("stroke", "url(#arrow-gradient)");
            arrowLine.setAttribute("stroke-width", "4");
            arrowLine.setAttribute("stroke-linecap", "round");
            arrowLine.setAttribute("marker-end", "url(#" + arrowId + ")");
            arrowLine.setAttribute("opacity", "0");
            arrowLine.setAttribute("x1", x1);
            arrowLine.setAttribute("y1", y1);
            arrowLine.setAttribute("x2", x2);
            arrowLine.setAttribute("y2", y2);
            arrowLine.setAttribute("filter", "url(#arrow-glow)");
            arrowLine.setAttribute("data-arrow", "enhanced");
            arrowLine.setAttribute("cgHash", `${size}, ${size},` + src + `,` + dst + `,enhanced`);

            // Add pulsing animation
            var animate = document.createElementNS("http://www.w3.org/2000/svg", "animate");
            animate.setAttribute("attributeName", "opacity");
            animate.setAttribute("values", "0;1;0.7;1");
            animate.setAttribute("dur", "1.5s");
            animate.setAttribute("repeatCount", "indefinite");
            arrowLine.appendChild(animate);

            // Add stroke-width animation for pulse effect
            var animateWidth = document.createElementNS("http://www.w3.org/2000/svg", "animate");
            animateWidth.setAttribute("attributeName", "stroke-width");
            animateWidth.setAttribute("values", "4;6;4");
            animateWidth.setAttribute("dur", "2s");
            animateWidth.setAttribute("repeatCount", "indefinite");
            arrowLine.appendChild(animateWidth);

            g.appendChild(arrowLine);

            // Add subtle move highlight on source and destination squares
            function addSquareHighlight(square, color, opacity) {
                var existingHighlight = document.querySelector(`[data-highlight="${square}"]`);
                if (existingHighlight) existingHighlight.remove();
                
                var highlight = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                highlight.setAttribute("cx", square === src ? x1 : x2);
                highlight.setAttribute("cy", square === src ? y1 : y2);
                highlight.setAttribute("r", "0.4");
                highlight.setAttribute("fill", color);
                highlight.setAttribute("opacity", opacity);
                highlight.setAttribute("data-highlight", square);
                highlight.setAttribute("data-arrow", "enhanced");
                
                var pulseAnim = document.createElementNS("http://www.w3.org/2000/svg", "animate");
                pulseAnim.setAttribute("attributeName", "r");
                pulseAnim.setAttribute("values", "0.3;0.5;0.3");
                pulseAnim.setAttribute("dur", "2s");
                pulseAnim.setAttribute("repeatCount", "indefinite");
                highlight.appendChild(pulseAnim);
                
                g.appendChild(highlight);
            }
            
            addSquareHighlight(src, "#ffaa00", "0.6");  // Orange for source
            addSquareHighlight(dst, "#00ff88", "0.8");  // Green for destination
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
