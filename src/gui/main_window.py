"""Main GUI Window for Chess Bot"""

import threading
import tkinter as tk
from tkinter import ttk
from typing import Optional

import chess
from loguru import logger

from .widgets.chess_board import ChessBoardWidget
from .widgets.game_info import GameInfoWidget
from .widgets.log_panel import LogPanelWidget
from .widgets.move_history import MoveHistoryWidget
from .widgets.result_popup import show_game_result


class ChessBotGUI:
    """Main GUI application for the chess bot"""

    def __init__(self, game_manager=None):
        self.game_manager = game_manager
        self._create_main_window()
        self._setup_layout()
        self._setup_callbacks()

        # State tracking
        self.current_board = chess.Board()
        self.our_color = "white"
        self.current_suggestion = None
        self.is_running = False

    def _create_main_window(self):
        """Create and configure the main window"""
        self.root = tk.Tk()
        self.root.title("Lichess Chess Bot")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)
        self.root.configure(bg="#2B2B2B")

        # Set window icon if available
        try:
            self.root.iconbitmap("assets/icon.ico")
        except:
            pass

        # Configure main grid - clean two-panel layout
        self.root.grid_columnconfigure(0, weight=1)  # Left panel - Board + Game Info
        self.root.grid_columnconfigure(1, weight=1)  # Right panel - Logs + History
        self.root.grid_rowconfigure(0, weight=1)

    def _setup_layout(self):
        """Setup the main layout with all widgets"""

        # Left panel - Board + Game Info
        left_frame = tk.Frame(self.root, bg="#2B2B2B")
        left_frame.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(0, weight=3)  # Board gets most space
        left_frame.grid_rowconfigure(1, weight=1)  # Game info smaller

        # Chess board
        board_frame = tk.Frame(left_frame, bg="#2B2B2B")
        board_frame.grid(row=0, column=0, pady=(0, 5), sticky="nsew")
        board_frame.grid_columnconfigure(0, weight=1)
        board_frame.grid_rowconfigure(0, weight=1)

        self.chess_board = ChessBoardWidget(board_frame)
        self.chess_board.grid(row=0, column=0, sticky="nsew")

        # Game info panel
        self.game_info = GameInfoWidget(left_frame)
        self.game_info.grid(row=1, column=0, sticky="nsew")

        # Right panel - Logs + Move History
        right_frame = tk.Frame(self.root, bg="#2B2B2B")
        right_frame.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(0, weight=2)  # Logs get more space
        right_frame.grid_rowconfigure(1, weight=1)  # Move history smaller

        # Log panel
        self.log_panel = LogPanelWidget(right_frame)
        self.log_panel.grid(row=0, column=0, pady=(0, 5), sticky="nsew")

        # Move history panel
        self.move_history = MoveHistoryWidget(right_frame)
        self.move_history.grid(row=1, column=0, sticky="nsew")

    def _setup_callbacks(self):
        """Setup callbacks between components"""
        if self.game_manager:
            # Register this GUI with the game manager for updates
            self.game_manager.set_gui_callback(self.update_from_game_manager)

            # Auto-start the bot
            self.root.after(1000, self._auto_start_bot)

    def _auto_start_bot(self):
        """Auto-start the bot after GUI is loaded"""
        if not self.is_running and self.game_manager:
            self.is_running = True
            self.log_panel.add_log("Auto-starting chess bot...", "success")

            # Start game manager in separate thread
            threading.Thread(target=self._run_game_manager, daemon=True).start()

    def _run_game_manager(self):
        """Run the game manager in a separate thread"""
        try:
            if self.game_manager:
                self.game_manager.start()
        except Exception as e:
            self.log_panel.add_log(f"Game manager error: {e}", "error")
            self.is_running = False

    def update_from_game_manager(self, update_data: dict):
        """Update GUI from game manager events"""
        try:
            update_type = update_data.get("type")

            if update_type == "board_update":
                self.update_board(
                    update_data.get("board"), update_data.get("last_move")
                )

            elif update_type == "suggestion":
                self.update_suggestion(
                    update_data.get("move"), update_data.get("evaluation")
                )

            elif update_type == "game_info":
                self.update_game_info(update_data)

            elif update_type == "move_played":
                self.add_move_to_history(
                    update_data.get("move"),
                    update_data.get("move_number"),
                    update_data.get("is_white"),
                )

            elif update_type == "game_start":
                self.move_history.clear_history()

            elif update_type == "game_finished":
                self.show_game_result(update_data)

            elif update_type == "log":
                self.log_panel.add_log(
                    update_data.get("message", ""), update_data.get("level", "info")
                )

        except Exception as e:
            logger.error(f"GUI update error: {e}")

    def update_board(self, board: chess.Board, last_move: Optional[chess.Move] = None):
        """Update the chess board display"""
        if board:
            self.current_board = board.copy()
            self.chess_board.update_position(board, last_move)

            # Clear suggestion arrow when a move has been made
            if last_move:
                self.chess_board.clear_suggestion()
                self.current_suggestion = None

    def update_suggestion(self, move: chess.Move, evaluation: dict = None):
        """Update the current engine suggestion"""
        self.current_suggestion = move
        if move:
            self.chess_board.show_suggestion(move)
            self.game_info.update_suggestion(move, evaluation)
        else:
            self.chess_board.clear_suggestion()

    def update_game_info(self, info: dict):
        """Update game information panel"""
        self.game_info.update_info(info)

        # Update our color if provided
        if "our_color" in info:
            self.our_color = info["our_color"]
            self.chess_board.set_orientation(self.our_color)

    def add_log(self, message: str, level: str = "info"):
        """Add a log message to the log panel"""
        self.log_panel.add_log(message, level)

    def add_move_to_history(self, move: chess.Move, move_number: int, is_white: bool):
        """Add a move to the move history"""
        if move:
            self.move_history.add_move(move, move_number, is_white)

    def show_game_result(self, result_data: dict):
        """Show the game result messagebox"""
        try:
            show_game_result(result_data)
        except Exception as e:
            logger.error(f"Error showing game result: {e}")
            # Fallback - just log to console
            score = result_data.get("score", "Unknown")
            reason = result_data.get("reason", "Unknown")
            self.add_log(f"Game finished: {score} - {reason}", "success")

    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()

    def destroy(self):
        """Clean up and destroy the GUI"""
        if self.root:
            self.root.destroy()
