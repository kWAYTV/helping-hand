"""Main GUI window for the chess bot"""

import os
import queue
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from typing import Any, Dict, Optional

import chess
from loguru import logger

from ..utils.helpers import get_icon_path
from .chess_board import ChessBoardWidget
from .move_history import MoveHistoryPanel
from .status_panel import StatusPanel


class ChessBotGUI:
    """Main GUI window for the chess bot"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Chess Bot - Helping Hand")
        self.root.geometry("1200x800")
        self.root.configure(bg="#2b2b2b")

        # Set window icon
        try:
            icon_path = get_icon_path()
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
                logger.debug(f"Window icon set: {icon_path}")
            else:
                logger.warning(f"Icon file not found: {icon_path}")
        except Exception as e:
            logger.warning(f"Failed to set window icon: {e}")

        # Application state
        self.board_state = chess.Board()
        self.game_active = False
        self.our_color = "white"
        self.move_history = []
        self.current_suggestion = None

        # Thread-safe communication
        self.gui_queue = queue.Queue()
        self.is_running = True

        # Create GUI components
        self._create_widgets()
        self._setup_layout()
        self._setup_styles()

        # Start GUI update loop
        self._start_update_loop()

        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_widgets(self):
        """Create all GUI widgets"""
        # Main frame
        self.main_frame = ttk.Frame(self.root)

        # Left panel - Chess board
        self.board_frame = ttk.LabelFrame(
            self.main_frame, text="Chess Board", padding=10
        )
        self.chess_board = ChessBoardWidget(self.board_frame, size=400)

        # Right panel - Game information
        self.info_frame = ttk.LabelFrame(
            self.main_frame, text="Game Information", padding=10
        )

        # Status panel
        self.status_panel = StatusPanel(self.info_frame)

        # Move history panel
        self.move_history_panel = MoveHistoryPanel(self.info_frame)

        # Console output
        self.console_frame = ttk.LabelFrame(
            self.info_frame, text="Console Output", padding=5
        )
        self.console_text = scrolledtext.ScrolledText(
            self.console_frame,
            height=15,
            width=50,
            bg="#1e1e1e",
            fg="#ffffff",
            font=("Consolas", 9),
            state=tk.DISABLED,
        )

        # Bottom status bar
        self.status_bar = ttk.Label(
            self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W, padding=(5, 2)
        )

    def _setup_layout(self):
        """Setup the layout of widgets"""
        # Main layout
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Configure grid weights
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=0)
        self.main_frame.grid_columnconfigure(1, weight=1)

        # Left panel - Chess board
        self.board_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.chess_board.pack(padx=10, pady=10)

        # Right panel - Information
        self.info_frame.grid(row=0, column=1, sticky="nsew")
        self.info_frame.grid_rowconfigure(2, weight=1)
        self.info_frame.grid_columnconfigure(0, weight=1)

        # Status panel
        self.status_panel.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Move history panel
        self.move_history_panel.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        # Console output
        self.console_frame.grid(row=2, column=0, sticky="nsew")
        self.console_frame.grid_rowconfigure(0, weight=1)
        self.console_frame.grid_columnconfigure(0, weight=1)
        self.console_text.grid(row=0, column=0, sticky="nsew")

        # Status bar
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _setup_styles(self):
        """Setup custom styles for the GUI"""
        style = ttk.Style()

        # Configure dark theme
        style.theme_use("clam")

        # Custom colors
        bg_color = "#2b2b2b"
        fg_color = "#ffffff"
        select_color = "#404040"

        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, foreground=fg_color)
        style.configure("TLabelFrame", background=bg_color, foreground=fg_color)
        style.configure("TLabelFrame.Label", background=bg_color, foreground=fg_color)

    def _start_update_loop(self):
        """Start the GUI update loop"""
        self._process_queue()
        self.root.after(50, self._start_update_loop)

    def _process_queue(self):
        """Process messages from the queue"""
        try:
            while True:
                message = self.gui_queue.get_nowait()
                self._handle_message(message)
        except queue.Empty:
            pass

    def _handle_message(self, message: Dict[str, Any]):
        """Handle a message from the game manager"""
        msg_type = message.get("type")

        if msg_type == "board_update":
            self._update_board(message["board"], message.get("highlight"))

        elif msg_type == "move_made":
            self._add_move(message["move"], message["player"])

        elif msg_type == "game_status":
            self.status_panel.update_status(message["status"])

        elif msg_type == "suggestion":
            self._show_suggestion(message["move"], message["evaluation"])

        elif msg_type == "console_log":
            self._add_console_log(message["level"], message["text"])

        elif msg_type == "game_result":
            self._show_game_result(message["result"])

    def _update_board(
        self, board: chess.Board, highlight_move: Optional[chess.Move] = None
    ):
        """Update the chess board display"""
        self.board_state = board.copy()
        self.chess_board.update_position(board, highlight_move)

    def _add_move(self, move: str, player: str):
        """Add a move to the history"""
        move_data = {
            "move": move,
            "player": player,
            "move_number": len(self.move_history) + 1,
        }
        self.move_history.append(move_data)
        self.move_history_panel.add_move(move_data)

    def _show_suggestion(self, move: chess.Move, evaluation: Optional[str] = None):
        """Show a move suggestion"""
        self.current_suggestion = move
        self.chess_board.show_suggestion(move)
        self.status_panel.update_suggestion(str(move), evaluation)

    def _add_console_log(self, level: str, text: str):
        """Add text to console output"""
        self.console_text.config(state=tk.NORMAL)

        # Color coding for different log levels
        if level == "ERROR":
            color = "#ff6b6b"
        elif level == "WARNING":
            color = "#feca57"
        elif level == "SUCCESS":
            color = "#48ca1a"
        elif level == "INFO":
            color = "#54a0ff"
        else:
            color = "#ffffff"

        # Insert text with color
        self.console_text.insert(tk.END, f"[{level}] {text}\n")
        self.console_text.see(tk.END)
        self.console_text.config(state=tk.DISABLED)

    def _show_game_result(self, result: str):
        """Show game result"""
        messagebox.showinfo("Game Result", result)
        self.status_panel.update_status(f"Game finished: {result}")

    def _on_closing(self):
        """Handle window closing"""
        self.is_running = False
        try:
            self.root.quit()
        except:
            pass
        try:
            self.root.destroy()
        except:
            pass

    def run(self):
        """Run the GUI main loop"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self._on_closing()

    # Public API for game manager integration
    def update_board_state(
        self, board: chess.Board, highlight_move: Optional[chess.Move] = None
    ):
        """Update board state (thread-safe)"""
        message = {"type": "board_update", "board": board, "highlight": highlight_move}
        self.gui_queue.put(message)

    def add_move(self, move: str, player: str):
        """Add move to history (thread-safe)"""
        message = {"type": "move_made", "move": move, "player": player}
        self.gui_queue.put(message)

    def update_game_status(self, status: str):
        """Update game status (thread-safe)"""
        message = {"type": "game_status", "status": status}
        self.gui_queue.put(message)

    def show_move_suggestion(self, move: chess.Move, evaluation: Optional[str] = None):
        """Show move suggestion (thread-safe)"""
        message = {"type": "suggestion", "move": move, "evaluation": evaluation}
        self.gui_queue.put(message)

    def log_message(self, level: str, text: str):
        """Log message to console (thread-safe)"""
        message = {"type": "console_log", "level": level, "text": text}
        self.gui_queue.put(message)

    def show_game_result(self, result: str):
        """Show game result (thread-safe)"""
        message = {"type": "game_result", "result": result}
        self.gui_queue.put(message)

    def set_our_color(self, color: str):
        """Set our playing color"""
        self.our_color = color
        self.chess_board.set_perspective(color == "white")

    def is_gui_running(self) -> bool:
        """Check if GUI is still running"""
        return self.is_running
