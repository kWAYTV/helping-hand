"""Game Manager - Main game flow and logic orchestration"""

import threading
from time import sleep

import chess
from loguru import logger
from selenium.webdriver.common.by import By

from ..auth.lichess import LichessAuth
from ..config import ConfigManager
from ..core.board import BoardHandler
from ..core.browser import BrowserManager
from ..core.engine import ChessEngine
from ..gui import ChessBotGUI, GUILogHandler
from ..input.keyboard_handler import KeyboardHandler
from ..utils.debug import DebugUtils
from ..utils.helpers import advanced_humanized_delay
from ..utils.resilience import (
    BrowserRecoveryManager,
    browser_retry,
    safe_execute,
    validate_game_state,
    with_browser_recovery,
)


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

        # Initialize resilience components
        self.browser_recovery_manager = BrowserRecoveryManager(self.browser_manager)

        self.board = chess.Board()
        self.current_game_active = False
        self._current_suggestion = None
        self._arrow_drawn = False

        # Initialize GUI if enabled
        self.gui = None
        self.gui_log_handler = None
        self.gui_thread = None
        self._initialize_gui()

    def _initialize_gui(self) -> None:
        """Initialize GUI if enabled"""
        if not self.config_manager.is_gui_enabled:
            logger.debug("GUI interface disabled in configuration")
            return

        try:
            # === GUI INITIALIZATION ===
            logger.info("Initializing graphical user interface")
            self.gui = ChessBotGUI()

            # Setup GUI log handler
            self.gui_log_handler = GUILogHandler(self.gui)
            self.gui_log_handler.install_handler()

            # Configure GUI with current settings
            mode = (
                "AutoPlay" if self.config_manager.is_autoplay_enabled else "Suggestion"
            )
            self.gui.update_game_status("Initializing...")
            self.gui.status_panel.update_bot_mode(mode)

            engine_config = self.config_manager.engine_config
            depth = engine_config.get("depth", "5")
            self.gui.status_panel.update_engine_depth(int(depth))

            logger.success("GUI interface ready")

        except Exception as e:
            logger.error(f"GUI initialization failed: {e}")
            self.gui = None

    def _start_game_thread(self) -> None:
        """Start game logic in separate thread (GUI runs in main thread)"""
        self.game_thread = threading.Thread(target=self._run_game_logic, daemon=True)
        self.game_thread.start()
        logger.debug("Game logic running in background thread")

    def start(self) -> None:
        """Start the chess bot application"""
        # === APPLICATION STARTUP ===
        logger.info("Chess Bot - Helping Hand starting")

        if self.gui:
            # GUI mode: Run GUI in main thread, game logic in background
            self._start_game_thread()
            logger.info("Running with graphical interface")

            try:
                self.gui.run()
            except KeyboardInterrupt:
                logger.info("Application closed by user")
            finally:
                self.cleanup()
        else:
            # Console mode: Run game logic directly
            logger.info("Running in console mode")
            self._run_game_logic()

    def _run_game_logic(self) -> None:
        """Run the main game logic (in separate thread when GUI is active)"""
        try:
            # === CONFIGURATION DISPLAY ===
            if self.gui and self.gui.is_gui_running():
                self.gui.update_game_status("Starting application...")
                self.gui.set_activity_status("Initializing...")

            if self.config_manager.is_autoplay_enabled:
                logger.info("Bot Mode: AutoPlay (fully automated)")
            else:
                move_key = self.config_manager.move_key
                logger.info(
                    f"Bot Mode: Suggestion (manual confirmation with '{move_key}' key)"
                )

            # === SYSTEM INITIALIZATION ===
            logger.debug("Initializing input handler")
            self.keyboard_handler.start_listening()

            # Update system status
            if self.gui and self.gui.is_gui_running():
                engine_depth = self.config_manager.get("engine", "depth", 5)
                self.gui.set_system_status("Initialized", int(engine_depth))

            # === LICHESS CONNECTION ===
            logger.info("Connecting to Lichess.org")
            if self.gui and self.gui.is_gui_running():
                self.gui.update_game_status("Navigating to Lichess...")
                self.gui.set_activity_status("Connecting to Lichess...")

            try:
                self.browser_manager.navigate_to("https://www.lichess.org")
                if self.gui and self.gui.is_gui_running():
                    self.gui.set_connection_status(True, "lichess.org")
            except Exception as e:
                logger.error(f"Failed to navigate to Lichess: {e}")
                if self.gui and self.gui.is_gui_running():
                    self.gui.set_connection_status(False, "Connection failed")
                if self.browser_recovery_manager.attempt_browser_recovery():
                    logger.info("Retrying navigation after browser recovery")
                    self.browser_manager.navigate_to("https://www.lichess.org")
                    if self.gui and self.gui.is_gui_running():
                        self.gui.set_connection_status(True, "lichess.org")
                else:
                    raise

            # === COOKIE STATUS ===
            cookie_info = self.browser_manager.get_cookies_info()
            if cookie_info["exists"]:
                logger.debug(
                    f"Found saved session ({cookie_info['count']} cookies, {cookie_info['file_size']} bytes)"
                )
            else:
                logger.debug(
                    "No saved session found - will use username/password authentication"
                )

            # === AUTHENTICATION ===
            logger.info("Authenticating with Lichess")
            if self.gui and self.gui.is_gui_running():
                self.gui.set_activity_status("Authenticating...")

            try:
                if not self.lichess_auth.is_logged_in():
                    self.lichess_auth.login()
                    logger.success("Authentication successful")
                    if self.gui and self.gui.is_gui_running():
                        self.gui.set_connection_status(True, "Authenticated")
                else:
                    logger.success("Already authenticated")
                    if self.gui and self.gui.is_gui_running():
                        self.gui.set_connection_status(True, "Already logged in")
            except Exception as e:
                logger.error(f"Authentication failed: {e}")
                if self.gui and self.gui.is_gui_running():
                    self.gui.set_connection_status(False, "Auth failed")
                raise

            # === GAME SEARCH ===
            logger.info("Looking for games...")
            if self.gui and self.gui.is_gui_running():
                self.gui.set_activity_status("Searching for games...")

            self.start_new_game()

        except Exception as e:
            logger.error(f"Game logic error: {e}")
            if self.gui and self.gui.is_gui_running():
                self.gui.update_game_status(f"Error: {e}")
            raise

    def start_new_game(self) -> None:
        """Start a new game with enhanced error handling"""
        # === NEW GAME INITIALIZATION ===
        logger.info("Starting new game")
        self.board.reset()
        self.current_game_active = True

        # Wait for game interface to be ready with retries
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                if self.board_handler.wait_for_game_ready():
                    break
                else:
                    logger.warning(
                        f"Game interface not ready (attempt {attempt + 1}/{max_attempts})"
                    )
                    if attempt < max_attempts - 1:
                        sleep(2)
                    else:
                        logger.error(
                            "Game interface failed to initialize after all attempts"
                        )
                        return
            except Exception as e:
                logger.error(
                    f"Error waiting for game ready (attempt {attempt + 1}): {e}"
                )
                if (
                    attempt < max_attempts - 1
                    and self.browser_recovery_manager.attempt_browser_recovery()
                ):
                    logger.info("Retrying after browser recovery")
                    continue
                else:
                    logger.error("Failed to start new game")
                    return

        # === PLAYER COLOR DETECTION ===
        try:
            our_color = self.board_handler.determine_player_color()
        except Exception as e:
            logger.error(f"Failed to determine player color: {e}")
            logger.warning("Defaulting to White")
            our_color = "W"

        # Update GUI with our playing color
        if self.gui and self.gui.is_gui_running():
            color_name = "White" if our_color == "W" else "Black"
            self.gui.status_panel.update_our_color(color_name)
            self.gui.set_our_color(color_name.lower())
            self.gui.set_activity_status(f"Playing as {color_name}")

        # === GAME START ===
        try:
            self.play_game(our_color)
        except Exception as e:
            logger.error(f"Game play failed: {e}")
            self.debug_utils.save_debug_info(self.browser_manager.driver, 0, self.board)

            # Stop timers and update status on game error
            if self.gui and self.gui.is_gui_running():
                self.gui.stop_timers()
                self.gui.set_activity_status("Game error occurred")
                self.gui.set_game_statistics(0, 0)

            # Attempt recovery and restart
            if self.browser_recovery_manager.attempt_browser_recovery():
                logger.info("Attempting to restart game after recovery")
                self.start_new_game()
            else:
                logger.error("Could not recover from game error")

    def play_game(self, our_color: str) -> None:
        """Main game playing loop"""
        # === GAME SETUP ===
        logger.info(
            f"Game started - playing as {'White' if our_color == 'W' else 'Black'}"
        )

        # Sync board state with current position
        move_number = self.board_handler.get_previous_moves(self.board)
        logger.debug(f"Board synchronized - starting at move {move_number}")

        # Update GUI with initial board state
        if self.gui and self.gui.is_gui_running():
            self.gui.update_board_state(self.board)
            self.gui.update_game_status("Game in progress")
            self.gui.start_game_timer()  # Start the game timer
            self.gui.set_activity_status("Game in progress")
            # Initialize game statistics
            total_moves = len(self.board.move_stack)
            our_moves = sum(
                1
                for i, _ in enumerate(self.board.move_stack)
                if (i % 2 == 0 and our_color == "W")
                or (i % 2 == 1 and our_color == "B")
            )
            self.gui.set_game_statistics(total_moves, our_moves)

        # Save session after successful game start
        logger.debug("Saving authentication session")
        self.browser_manager.save_cookies()

        # === GAME STATUS LOGGING ===
        if move_number == 1:
            if our_color == "W":
                logger.info("Fresh game started - we play first as White")
            else:
                logger.info("Fresh game started - waiting for White's first move")
        else:
            if self._is_our_turn(our_color):
                logger.info(f"Joined game in progress - our turn (move {move_number})")
            else:
                logger.info(
                    f"Joined game in progress - waiting for opponent (move {move_number})"
                )

        # === MAIN GAME LOOP ===
        consecutive_errors = 0
        max_consecutive_errors = 5

        while not self.board_handler.is_game_over():
            try:
                # Validate game state periodically
                if not validate_game_state(self.board, move_number):
                    logger.warning("Game state validation failed - attempting recovery")
                    self.debug_utils.save_debug_info(
                        self.browser_manager.driver, move_number, self.board
                    )

                    # Try to recover by refreshing the page
                    if self.browser_recovery_manager.is_browser_healthy():
                        logger.info("Refreshing page to recover game state")
                        self.browser_manager.driver.refresh()
                        sleep(5)  # Wait for page to load
                        continue
                    else:
                        logger.error("Browser unhealthy - attempting recovery")
                        if not self.browser_recovery_manager.attempt_browser_recovery():
                            logger.error("Browser recovery failed - exiting game")
                            break

                our_turn = self._is_our_turn(our_color)
                previous_move_number = move_number

                if our_turn:
                    move_number = self._handle_our_turn(move_number, our_color)
                else:
                    move_number = self._handle_opponent_turn(move_number, our_color)

                # Prevent infinite loops
                if move_number == previous_move_number:
                    sleep(0.1)

                # Reset error counter on successful iteration
                consecutive_errors = 0

            except Exception as e:
                consecutive_errors += 1
                logger.error(
                    f"Game loop error (attempt {consecutive_errors}/{max_consecutive_errors}): {e}"
                )

                if consecutive_errors >= max_consecutive_errors:
                    logger.error("Too many consecutive errors - exiting game")
                    self.debug_utils.save_debug_info(
                        self.browser_manager.driver, move_number, self.board
                    )
                    break

                # Try browser recovery for critical errors
                if not self.browser_recovery_manager.is_browser_healthy():
                    logger.warning("Browser unhealthy - attempting recovery")
                    if self.browser_recovery_manager.attempt_browser_recovery():
                        logger.info("Browser recovery successful - continuing game")
                        continue
                    else:
                        logger.error("Browser recovery failed - exiting game")
                        break

                # Small delay before retrying
                sleep(2)

        # === GAME COMPLETION ===
        logger.info("Game completed")

        # Stop timers when game ends
        if self.gui and self.gui.is_gui_running():
            self.gui.stop_timers()
            self.gui.set_activity_status("Game completed")
            self.gui.set_system_status("Waiting for next game")

        self._log_game_result()
        logger.info("Waiting for next game")

        # Reset for next game
        if self.gui and self.gui.is_gui_running():
            self.gui.set_activity_status("Searching for new game...")

        self.start_new_game()

    def _is_our_turn(self, our_color: str) -> bool:
        """Check if it's our turn to move"""
        # First check the interface state for more accurate detection
        interface_turn = self.board_handler.is_our_turn_via_interface()

        if interface_turn is not None:
            # Interface gives us a definitive answer
            board_turn = (self.board.turn and our_color == "W") or (
                not self.board.turn and our_color == "B"
            )

            if interface_turn != board_turn:
                # Interface and board state disagree - interface is more reliable
                logger.debug(
                    f"Turn state mismatch: interface says {'our' if interface_turn else 'opponent'} turn, board says {'our' if board_turn else 'opponent'} turn"
                )
                logger.debug("Using interface state (more reliable)")
                return interface_turn
            else:
                # Both agree - good synchronization
                logger.debug(
                    f"Turn state synchronized: {'our' if interface_turn else 'opponent'} turn"
                )
                return interface_turn

        # Fallback to board state if interface check fails
        board_turn = (self.board.turn and our_color == "W") or (
            not self.board.turn and our_color == "B"
        )
        logger.debug(
            f"Using board state for turn detection: {'our' if board_turn else 'opponent'} turn"
        )
        return board_turn

    def _handle_our_turn(self, move_number: int, our_color: str) -> int:
        """Handle our turn logic"""
        # Reset move timer when it becomes our turn
        if self.gui and self.gui.is_gui_running():
            self.gui.reset_move_timer()
            self.gui.set_activity_status(
                "Thinking..."
                if self.config_manager.is_autoplay_enabled
                else "Awaiting move confirmation"
            )

        # Check if we already made the move
        move_text = self.board_handler.check_for_move(move_number)
        if move_text:
            logger.debug(f"Move {move_number} already executed: {move_text}")
            self.board_handler.clear_arrow()

            if self.board_handler.validate_and_push_move(
                self.board, move_text, move_number, True
            ):
                # Update game statistics after our move
                if self.gui and self.gui.is_gui_running():
                    total_moves = len(self.board.move_stack)
                    our_moves = sum(
                        1
                        for i, _ in enumerate(self.board.move_stack)
                        if (i % 2 == 0 and our_color == "W")
                        or (i % 2 == 1 and our_color == "B")
                    )
                    self.gui.set_game_statistics(total_moves, our_moves)
                return move_number + 1
            else:
                return move_number

        # === MOVE CALCULATION ===
        engine_depth = self.config_manager.get(
            "engine", "depth", self.config_manager.get("engine", "Depth", 5)
        )
        logger.debug(f"Calculating move (depth: {engine_depth})")

        # Update engine status
        if self.gui and self.gui.is_gui_running():
            self.gui.set_system_status("Analyzing...", int(engine_depth))

        advanced_humanized_delay("engine thinking", self.config_manager, "thinking")

        result = self.chess_engine.get_best_move(self.board)
        move_str = str(result.move)
        src_square = move_str[:2]
        dst_square = move_str[2:]
        logger.info(f"Engine recommends: {result.move} ({src_square} → {dst_square})")

        # Update engine status back to ready
        if self.gui and self.gui.is_gui_running():
            self.gui.set_system_status("Ready", int(engine_depth))

        # Update GUI with suggestion
        if self.gui and self.gui.is_gui_running():
            self.gui.show_move_suggestion(result.move)

        # Handle move execution based on mode
        if self.config_manager.is_autoplay_enabled:
            return self._execute_auto_move(result.move, move_number, our_color)
        else:
            return self._handle_manual_move(result.move, move_number, our_color)

    def _execute_auto_move(
        self, move: chess.Move, move_number: int, our_color: str
    ) -> int:
        """Execute move automatically"""
        logger.info(f"Executing move: {move}")

        # Update activity status
        if self.gui and self.gui.is_gui_running():
            self.gui.set_activity_status("Executing move...")

        # Show arrow briefly if enabled, even in autoplay
        if self.config_manager.show_arrow:
            logger.debug("Displaying move preview")
            self.board_handler.draw_arrow(move, our_color)
            # Brief delay to show the arrow
            advanced_humanized_delay("showing arrow", self.config_manager, "base")

        self.board_handler.execute_move(move, move_number)
        self.board.push(move)

        # Update GUI and clear suggestion arrow
        if self.gui and self.gui.is_gui_running():
            self.gui.update_board_state(self.board, move)
            self.gui.add_move(str(move), "us")
            self.gui.clear_move_suggestion()  # Clear suggestion arrow after execution
            # Update statistics after our move
            total_moves = len(self.board.move_stack)
            our_moves = sum(
                1
                for i, _ in enumerate(self.board.move_stack)
                if (i % 2 == 0 and our_color == "W")
                or (i % 2 == 1 and our_color == "B")
            )
            self.gui.set_game_statistics(total_moves, our_moves)
            self.gui.set_activity_status("Waiting for opponent...")

        return move_number + 1

    def _handle_manual_move(
        self, move: chess.Move, move_number: int, our_color: str
    ) -> int:
        """Handle manual move execution"""
        # Show arrow if enabled (only draw once per turn)
        if not hasattr(self, "_current_suggestion") or self._current_suggestion != move:
            self._current_suggestion = move
            self._arrow_drawn = False

        if self.config_manager.show_arrow and not self._arrow_drawn:
            logger.debug("Displaying move suggestion")
            self.board_handler.draw_arrow(move, our_color)
            self._arrow_drawn = True

        # Check for key press
        if self.keyboard_handler.should_make_move():
            logger.info(f"Manual confirmation received - executing: {move}")

            # Update activity status
            if self.gui and self.gui.is_gui_running():
                self.gui.set_activity_status("Executing confirmed move...")

            self.board_handler.execute_move(move, move_number)
            self.keyboard_handler.reset_move_state()
            self.board.push(move)

            # Update GUI and clear suggestion arrow
            if self.gui and self.gui.is_gui_running():
                self.gui.update_board_state(self.board, move)
                self.gui.add_move(str(move), "us")
                self.gui.clear_move_suggestion()  # Clear suggestion arrow after execution
                # Update statistics after our move
                total_moves = len(self.board.move_stack)
                our_moves = sum(
                    1
                    for i, _ in enumerate(self.board.move_stack)
                    if (i % 2 == 0 and our_color == "W")
                    or (i % 2 == 1 and our_color == "B")
                )
                self.gui.set_game_statistics(total_moves, our_moves)
                self.gui.set_activity_status("Waiting for opponent...")

            # Reset suggestion tracking
            self._current_suggestion = None
            self._arrow_drawn = False

            return move_number + 1
        else:
            # Show suggestion and wait for input
            move_key = self.config_manager.move_key
            move_str = str(move)
            src_square = move_str[:2]
            dst_square = move_str[2:]
            logger.debug(
                f"Awaiting confirmation for: {move} ({src_square} → {dst_square}) - press '{move_key}'"
            )
            sleep(0.1)  # Small delay to avoid spam

            return move_number

    def _handle_opponent_turn(self, move_number: int, our_color: str) -> int:
        """Handle opponent's turn"""
        self.board_handler.clear_arrow()

        # Clear any GUI suggestions when it's opponent's turn
        if self.gui and self.gui.is_gui_running():
            self.gui.clear_move_suggestion()
            self.gui.reset_move_timer()  # Reset move timer for opponent's turn
            self.gui.set_activity_status("Opponent thinking...")

        move_text = self.board_handler.check_for_move(move_number)
        if move_text:
            logger.info(f"Opponent played: {move_text}")

            if self.board_handler.validate_and_push_move(
                self.board, move_text, move_number, False
            ):
                # Update GUI for opponent move and statistics
                if self.gui and self.gui.is_gui_running():
                    self.gui.update_board_state(self.board)
                    self.gui.add_move(move_text, "opponent")
                    # Update game statistics
                    total_moves = len(self.board.move_stack)
                    our_moves = sum(
                        1
                        for i, _ in enumerate(self.board.move_stack)
                        if (i % 2 == 0 and our_color == "W")
                        or (i % 2 == 1 and our_color == "B")
                    )
                    self.gui.set_game_statistics(total_moves, our_moves)
                return move_number + 1

        return move_number

    def _log_game_result(self) -> None:
        """Log the game result when game ends"""
        try:
            # === GAME RESULT EXTRACTION ===
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

            logger.success(f"Game Result: {score} | {result}")

            # Update GUI with game result
            if self.gui and self.gui.is_gui_running():
                self.gui.show_game_result(f"{score} | {result}")

        except Exception as e:
            logger.debug(f"Could not extract detailed game result: {e}")
            logger.success("Game finished")

            # Update GUI with generic result
            if self.gui and self.gui.is_gui_running():
                self.gui.show_game_result("Game finished")

    def cleanup(self) -> None:
        """Clean up all resources"""
        logger.info("Cleaning up resources...")

        # Stop timers
        if self.gui and self.gui.is_gui_running():
            self.gui.stop_timers()
            self.gui.set_activity_status("Shutting down...")
            self.gui.set_connection_status(False, "Disconnecting")
            self.gui.set_system_status("Stopping")

        # Stop keyboard handler
        if hasattr(self, "keyboard_handler") and self.keyboard_handler:
            safe_execute(
                self.keyboard_handler.stop_listening,
                log_errors=True,
                operation_name="keyboard handler cleanup",
            )

        # Close chess engine
        if hasattr(self, "chess_engine") and self.chess_engine:
            safe_execute(
                self.chess_engine.quit,
                log_errors=True,
                operation_name="chess engine cleanup",
            )

        # Close browser (most critical)
        if hasattr(self, "browser_manager") and self.browser_manager:
            safe_execute(
                lambda: (
                    self.browser_manager.driver.quit()
                    if self.browser_manager.driver
                    else None
                ),
                log_errors=True,
                operation_name="browser cleanup",
            )

        # Close GUI
        if hasattr(self, "gui") and self.gui:
            safe_execute(
                self.gui._on_closing,
                log_errors=True,
                operation_name="GUI cleanup",
            )

        logger.success("Resource cleanup completed")
