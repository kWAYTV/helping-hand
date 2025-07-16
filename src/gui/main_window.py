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

        # Configure window for dark theme
        try:
            # Try to set dark title bar on Windows 10/11
            import platform

            if platform.system() == "Windows":
                self.root.tk.call("::tk::unsupported::DarkModeEnabled", True)
        except:
            pass  # Ignore if not supported

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
            insertbackground="#ffffff",  # Cursor color
            selectbackground="#404040",  # Selection background
            selectforeground="#ffffff",  # Selection text color
            borderwidth=1,
            relief="solid",
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

        # Dark theme color palette
        bg_dark = "#2b2b2b"  # Main background
        bg_darker = "#1e1e1e"  # Darker background for panels
        bg_lighter = "#404040"  # Lighter background for selections
        fg_primary = "#ffffff"  # Primary text color
        fg_secondary = "#cccccc"  # Secondary text color
        fg_muted = "#888888"  # Muted text color
        accent_color = "#0078d4"  # Accent color
        border_color = "#555555"  # Border color

        # Configure ttk styles
        style.configure("TFrame", background=bg_dark, borderwidth=0)
        style.configure("TLabel", background=bg_dark, foreground=fg_primary)
        style.configure(
            "TLabelFrame",
            background=bg_dark,
            foreground=fg_primary,
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "TLabelFrame.Label",
            background=bg_dark,
            foreground=fg_primary,
            font=("Arial", 10, "bold"),
        )

        # Button styles
        style.configure(
            "TButton",
            background=bg_lighter,
            foreground=fg_primary,
            borderwidth=1,
            focuscolor="none",
        )
        style.map(
            "TButton", background=[("active", accent_color), ("pressed", bg_darker)]
        )

        # Entry styles
        style.configure(
            "TEntry",
            background=bg_darker,
            foreground=fg_primary,
            insertcolor=fg_primary,
            borderwidth=1,
            relief="solid",
        )
        style.map(
            "TEntry", focuscolor=[("!focus", border_color), ("focus", accent_color)]
        )

        # Scrollbar styles
        style.configure(
            "TScrollbar",
            background=bg_lighter,
            troughcolor=bg_darker,
            borderwidth=1,
            arrowcolor=fg_primary,
        )
        style.map("TScrollbar", background=[("active", accent_color)])

        # Separator styles
        style.configure("TSeparator", background=border_color)

        # Notebook styles (if used)
        style.configure("TNotebook", background=bg_dark, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=bg_lighter,
            foreground=fg_primary,
            padding=[10, 5],
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", bg_dark), ("active", accent_color)],
        )

        # Configure console text colors
        self._setup_console_colors()

        # Apply dark theme to console scrollbar
        try:
            # Get the scrollbar from the ScrolledText widget
            scrollbar = self.console_text.vbar
            scrollbar.configure(
                bg="#404040",  # Background
                troughcolor="#1e1e1e",  # Trough color
                activebackground="#0078d4",  # Active background
                highlightthickness=0,  # Remove highlight
            )
        except:
            pass  # Ignore if scrollbar customization fails

    def _setup_console_colors(self):
        """Setup color tags for console text"""
        # Define color tags for different log levels
        self.console_text.tag_configure("ERROR", foreground="#ff6b6b")  # Red
        self.console_text.tag_configure("WARNING", foreground="#feca57")  # Yellow
        self.console_text.tag_configure("SUCCESS", foreground="#48ca1a")  # Green
        self.console_text.tag_configure("INFO", foreground="#54a0ff")  # Blue
        self.console_text.tag_configure("DEBUG", foreground="#a8a8a8")  # Gray
        self.console_text.tag_configure("TRACE", foreground="#888888")  # Darker Gray
        self.console_text.tag_configure("DEFAULT", foreground="#ffffff")  # White

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

        elif msg_type == "clear_suggestion":
            self.chess_board.clear_suggestion()
            self.status_panel.clear_suggestion()

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

        # Apply color tags
        self.console_text.insert(tk.END, f"[{level}] {text}\n", level)
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

    def clear_move_suggestion(self):
        """Clear move suggestion from board and status panel (thread-safe)"""
        message = {"type": "clear_suggestion"}
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
