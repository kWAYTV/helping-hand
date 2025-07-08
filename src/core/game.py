"""Game Manager - Main game flow and logic orchestration"""

from time import sleep

import chess
from loguru import logger
from selenium.webdriver.common.by import By

from ..auth.lichess import LichessAuth
from ..config import ConfigManager
from ..core.board import BoardHandler
from ..core.browser import BrowserManager
from ..core.engine import ChessEngine
from ..input.keyboard_handler import KeyboardHandler
from ..utils.debug import DebugUtils
from ..utils.helpers import advanced_humanized_delay


class GameManager:
    """Manages the overall game flow and coordinates all components"""

    def __init__(self):
        # Initialize all components
        self.config_manager = ConfigManager()
        self.browser_manager = BrowserManager()
        self.debug_utils = DebugUtils()
        self.board_handler = BoardHandler(
            self.browser_manager, self.debug_utils, self.config_manager
        )
        self.chess_engine = ChessEngine(self.config_manager)
        self.keyboard_handler = KeyboardHandler(self.config_manager)
        self.lichess_auth = LichessAuth(self.config_manager, self.browser_manager)

        self.board = chess.Board()
        self.current_game_active = False
        self._current_suggestion = None
        self._arrow_drawn = False

    def start(self) -> None:
        """Start the chess bot application"""
        logger.info("Starting chess bot application")

        # Log current configuration
        if self.config_manager.is_autoplay_enabled:
            logger.info("AutoPlay MODE: Bot will make moves automatically")
        else:
            move_key = self.config_manager.move_key
            logger.info(
                f"Suggestion MODE: Bot will suggest moves (press '{move_key}' to execute)"
            )

        # Start keyboard listener
        logger.debug("Starting keyboard listener")
        self.keyboard_handler.start_listening()

        # Navigate to Lichess
        logger.debug("Navigating to lichess.org")
        self.browser_manager.navigate_to("https://www.lichess.org")

        # Show cookie status
        cookie_info = self.browser_manager.get_cookies_info()
        if cookie_info["exists"]:
            logger.debug(
                f"Found saved cookies ({cookie_info['count']} cookies, {cookie_info['file_size']} bytes)"
            )
        else:
            logger.debug("No saved cookies found - will use username/password login")

        # Sign in
        if not self.lichess_auth.sign_in():
            logger.error("Failed to sign in to Lichess")
            return

        # Start game loop
        logger.info("Waiting for game to start")
        self.start_new_game()

    def start_new_game(self) -> None:
        """Start a new game"""
        logger.debug("Starting new game - resetting board")
        self.board.reset()
        self.current_game_active = True

        # Wait for game to be ready
        if not self.board_handler.wait_for_game_ready():
            logger.error("Failed to wait for game ready")
            return

        # Determine our color
        our_color = self.board_handler.determine_player_color()

        # Start playing
        self.play_game(our_color)

    def play_game(self, our_color: str) -> None:
        """Main game playing loop"""
        logger.debug(f"Starting play_game as {our_color}")

        # Get move input handle
        move_handle = self.board_handler.get_move_input_handle()
        if not move_handle:
            logger.error("Failed to get move input handle")
            return

            # Get previous moves to sync board state
        move_number = self.board_handler.get_previous_moves(self.board)
        logger.debug(f"Ready to play. Starting at move number: {move_number}")

        # Save cookies after successful game start (indicates successful login)
        logger.debug("Saving login cookies for faster future authentication")
        self.browser_manager.save_cookies()

        # If this is the very start of the game, log our turn status
        if move_number == 1:
            if our_color == "W":
                logger.info("Starting fresh game as White - we move first")
            else:
                logger.info(
                    "Starting fresh game as Black - waiting for White's first move"
                )

        # Main game loop
        while not self.board_handler.is_game_over():
            our_turn = self._is_our_turn(our_color)
            previous_move_number = move_number

            if our_turn:
                move_number = self._handle_our_turn(move_number, move_handle, our_color)
            else:
                move_number = self._handle_opponent_turn(move_number)

            # Prevent infinite loops
            if move_number == previous_move_number:
                sleep(0.1)

        # Game complete
        logger.debug("Game completed - follow-up element detected")
        self._log_game_result()
        self.chess_engine.quit()
        logger.debug("Chess engine stopped")
        logger.info("Game complete. Waiting for new game to start.")
        self.start_new_game()

    def _is_our_turn(self, our_color: str) -> bool:
        """Check if it's our turn to move"""
        return (self.board.turn and our_color == "W") or (
            not self.board.turn and our_color == "B"
        )

    def _handle_our_turn(self, move_number: int, move_handle, our_color: str) -> int:
        """Handle our turn logic"""
        # Check if we already made the move
        move_text = self.board_handler.check_for_move(move_number)
        if move_text:
            logger.debug(f"Our move detected on board at position {move_number}")
            self.board_handler.clear_arrow()

            if self.board_handler.validate_and_push_move(
                self.board, move_text, move_number, True
            ):
                return move_number + 1
            else:
                return move_number

        # Get best move from engine
        engine_depth = self.config_manager.get(
            "engine", "depth", self.config_manager.get("engine", "Depth", 5)
        )
        logger.debug(f"Our turn - calculating best move (depth: {engine_depth})")
        advanced_humanized_delay("engine thinking", self.config_manager, "thinking")

        result = self.chess_engine.get_best_move(self.board)
        move_str = str(result.move)
        src_square = move_str[:2]
        dst_square = move_str[2:]
        logger.info(f"Engine suggests: {result.move} ({src_square} → {dst_square})")

        # Handle move execution based on mode
        if self.config_manager.is_autoplay_enabled:
            return self._execute_auto_move(
                result.move, move_handle, move_number, our_color
            )
        else:
            return self._handle_manual_move(
                result.move, move_handle, move_number, our_color
            )

    def _execute_auto_move(
        self, move: chess.Move, move_handle, move_number: int, our_color: str
    ) -> int:
        """Execute move automatically"""
        logger.debug(f"AutoPlay enabled - making move: {move}")

        # Show arrow briefly if enabled, even in autoplay
        if self.config_manager.show_arrow:
            logger.debug("Showing move arrow before auto execution")
            self.board_handler.draw_arrow(move, our_color)
            # Brief delay to show the arrow
            advanced_humanized_delay("showing arrow", self.config_manager, "base")

        self.board_handler.execute_move(move, move_handle, move_number)
        self.board.push(move)

        return move_number + 1

    def _handle_manual_move(
        self, move: chess.Move, move_handle, move_number: int, our_color: str
    ) -> int:
        """Handle manual move execution"""
        # Show arrow if enabled (only draw once per turn)
        if not hasattr(self, "_current_suggestion") or self._current_suggestion != move:
            self._current_suggestion = move
            self._arrow_drawn = False

        if self.config_manager.show_arrow and not self._arrow_drawn:
            logger.debug("Showing move suggestion arrow")
            self.board_handler.draw_arrow(move, our_color)
            self._arrow_drawn = True

        # Check for key press
        if self.keyboard_handler.should_make_move():
            logger.info(f"Manual key press detected - making move: {move}")

            self.board_handler.execute_move(move, move_handle, move_number)
            self.keyboard_handler.reset_move_state()
            self.board.push(move)

            # Reset suggestion tracking
            self._current_suggestion = None
            self._arrow_drawn = False

            return move_number + 1
        else:
            # Just suggesting - show the move and wait
            move_key = self.config_manager.move_key
            move_str = str(move)
            src_square = move_str[:2]
            dst_square = move_str[2:]
            logger.debug(
                f"Suggesting move: {move} ({src_square} → {dst_square}) (press {move_key} to execute)"
            )
            logger.info(
                f"Suggest move: {move} ({src_square} → {dst_square}) - press {move_key} to execute"
            )
            sleep(0.1)  # Small delay to avoid spam

            return move_number

    def _handle_opponent_turn(self, move_number: int) -> int:
        """Handle opponent's turn"""
        self.board_handler.clear_arrow()

        move_text = self.board_handler.check_for_move(move_number)
        if move_text:
            logger.info(f"Opponent move detected at position {move_number}")

            if self.board_handler.validate_and_push_move(
                self.board, move_text, move_number, False
            ):
                return move_number + 1

        return move_number

    def _log_game_result(self) -> None:
        """Log the game result when game ends"""
        try:
            # Get score using driver directly
            score_element = self.browser_manager.driver.find_element(
                By.XPATH, "/html/body/div[2]/main/div[1]/rm6/l4x/div/p[1]"
            )
            score = score_element.text if score_element else "Score not found"

            # Get result reason using driver directly
            result_element = self.browser_manager.driver.find_element(
                By.XPATH, "/html/body/div[2]/main/div[1]/rm6/l4x/div/p[2]"
            )
            result = result_element.text if result_element else "Result not found"

            logger.success(f"GAME FINISHED - {score} | {result}")

        except Exception as e:
            logger.debug(f"Could not extract game result: {e}")
            logger.info("GAME FINISHED - Result details not available")

    def cleanup(self) -> None:
        """Clean up resources"""
        logger.info("Cleaning up resources")

        if self.keyboard_handler:
            self.keyboard_handler.stop_listening()

        if self.chess_engine:
            self.chess_engine.quit()

        if self.browser_manager:
            self.browser_manager.close()
