"""Main GUI window for the chess bot"""

import os
import queue
import threading
import time
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
        self.root.geometry("1200x750")  # More compact with tabbed interface
        self.root.configure(bg="#2b2b2b")
        self.root.minsize(1000, 650)  # Reduced minimum size for compact layout

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

        # Timer state
        self.game_start_time = None
        self.move_start_time = None
        self.timer_running = False

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
        # Main container with padding
        self.main_container = ttk.Frame(self.root)

        # Left panel - Chess board
        self.board_frame = ttk.LabelFrame(
            self.main_container, text="Chess Board", padding=15
        )
        self.chess_board = ChessBoardWidget(
            self.board_frame, size=500
        )  # Balanced size for compact tabbed layout

        # Right panel - Tabbed interface for compact layout
        self.info_frame = ttk.Frame(self.main_container)

        # Create notebook (tab container)
        self.notebook = ttk.Notebook(self.info_frame)

        # Tab 1: Game Status
        self.status_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.status_tab, text="🎯 Status")
        self.status_panel = StatusPanel(self.status_tab)

        # Tab 2: Move History
        self.history_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.history_tab, text="📋 History")
        self.move_history_panel = MoveHistoryPanel(self.history_tab)

        # Tab 3: Console Output
        self.console_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.console_tab, text="💻 Console")

        # Console text widget with full height utilization
        self.console_text = scrolledtext.ScrolledText(
            self.console_tab,
            bg="#1e1e1e",
            fg="#ffffff",
            font=("Consolas", 9),
            state=tk.DISABLED,
            insertbackground="#ffffff",
            selectbackground="#404040",
            selectforeground="#ffffff",
            borderwidth=1,
            relief="solid",
            wrap=tk.WORD,
        )

        # Enhanced bottom status bar with multiple sections
        self.status_bar_frame = ttk.Frame(self.root)

        # Status bar sections
        self.activity_status = ttk.Label(
            self.status_bar_frame,
            text="🤖 Ready",
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(8, 3),
            font=("Arial", 9),
        )

        self.connection_status = ttk.Label(
            self.status_bar_frame,
            text="🌐 Disconnected",
            relief=tk.SUNKEN,
            anchor=tk.CENTER,
            padding=(8, 3),
            font=("Arial", 9),
        )

        self.game_stats = ttk.Label(
            self.status_bar_frame,
            text="📊 No game active",
            relief=tk.SUNKEN,
            anchor=tk.CENTER,
            padding=(8, 3),
            font=("Arial", 9),
        )

        self.system_info = ttk.Label(
            self.status_bar_frame,
            text="⚙️ Engine: Ready",
            relief=tk.SUNKEN,
            anchor=tk.E,
            padding=(8, 3),
            font=("Arial", 9),
        )

    def _setup_layout(self):
        """Setup the layout of widgets"""
        # Main layout
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Configure main grid weights for responsive layout
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(
            0, weight=0, minsize=530
        )  # Fixed chess board area for compact layout
        self.main_container.grid_columnconfigure(
            1, weight=1, minsize=450
        )  # Flexible info area - compact with tabs

        # Left panel - Chess board (fixed size)
        self.board_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.chess_board.pack(anchor="center")

        # Right panel - Tabbed interface
        self.info_frame.grid(row=0, column=1, sticky="nsew")

        # Configure right panel for single notebook
        self.info_frame.grid_rowconfigure(0, weight=1)
        self.info_frame.grid_columnconfigure(0, weight=1)

        # Pack notebook to fill entire right panel
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Configure individual tabs
        # Status tab
        self.status_tab.grid_rowconfigure(0, weight=1)
        self.status_tab.grid_columnconfigure(0, weight=1)
        self.status_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # History tab
        self.history_tab.grid_rowconfigure(0, weight=1)
        self.history_tab.grid_columnconfigure(0, weight=1)
        self.move_history_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Console tab
        self.console_tab.grid_rowconfigure(0, weight=1)
        self.console_tab.grid_columnconfigure(0, weight=1)
        self.console_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Status bar (bottom of window)
        self.status_bar_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(2, 0))

        # Configure status bar grid weights
        self.status_bar_frame.grid_columnconfigure(
            0, weight=2
        )  # Activity gets more space
        self.status_bar_frame.grid_columnconfigure(1, weight=1)  # Connection
        self.status_bar_frame.grid_columnconfigure(2, weight=1)  # Game stats
        self.status_bar_frame.grid_columnconfigure(3, weight=1)  # System info

        # Pack status bar sections
        self.activity_status.grid(row=0, column=0, sticky="ew", padx=(0, 2))
        self.connection_status.grid(row=0, column=1, sticky="ew", padx=2)
        self.game_stats.grid(row=0, column=2, sticky="ew", padx=2)
        self.system_info.grid(row=0, column=3, sticky="ew", padx=(2, 0))

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
        self._update_timers()
        self.root.after(50, self._start_update_loop)

    def _update_timers(self):
        """Update timer displays"""
        if self.timer_running and self.game_start_time:
            current_time = time.time()

            # Update game time
            game_elapsed = int(current_time - self.game_start_time)
            self.status_panel.update_game_time(game_elapsed)

            # Update move time
            if self.move_start_time:
                move_elapsed = int(current_time - self.move_start_time)
                self.status_panel.update_move_time(move_elapsed)

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
            # Update window title with current status
            try:
                self.root.title(f"Chess Bot - Helping Hand - {message['status']}")
            except:
                pass  # Ignore if window is closed

        elif msg_type == "suggestion":
            self._show_suggestion(message["move"], message["evaluation"])

        elif msg_type == "clear_suggestion":
            self.chess_board.clear_suggestion()
            self.status_panel.clear_suggestion()

        elif msg_type == "timer_start":
            self._start_game_timer()

        elif msg_type == "timer_stop":
            self._stop_timers()

        elif msg_type == "move_timer_reset":
            self._reset_move_timer()

        elif msg_type == "status_activity":
            self.update_activity_status(message["status"])

        elif msg_type == "status_connection":
            self.update_connection_status(
                message["connected"], message.get("details", "")
            )

        elif msg_type == "status_game_stats":
            self.update_game_statistics(
                message.get("moves_played", 0), message.get("our_moves", 0)
            )

        elif msg_type == "status_system":
            self.update_system_status(
                message.get("engine_status", "Ready"), message.get("depth")
            )

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

        # Auto-scroll to bottom and limit buffer size
        self.console_text.see(tk.END)

        # Limit console buffer to prevent memory issues (keep last 1000 lines)
        lines = self.console_text.get("1.0", tk.END).count("\n")
        if lines > 1000:
            # Delete first 100 lines
            self.console_text.delete("1.0", "101.0")

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

    def _start_game_timer(self):
        """Start the game timer"""
        self.game_start_time = time.time()
        self.move_start_time = time.time()
        self.timer_running = True

    def _stop_timers(self):
        """Stop all timers"""
        self.timer_running = False
        self.game_start_time = None
        self.move_start_time = None
        self.status_panel.reset_timers()

    def _reset_move_timer(self):
        """Reset the move timer"""
        if self.timer_running:
            self.move_start_time = time.time()

    def update_activity_status(self, status: str):
        """Update activity status section"""
        self.activity_status.configure(text=f"🤖 {status}")

    def update_connection_status(self, connected: bool, details: str = ""):
        """Update connection status section"""
        if connected:
            text = f"🌐 Connected"
            if details:
                text += f" - {details}"
        else:
            text = f"🌐 Disconnected"
            if details:
                text += f" - {details}"
        self.connection_status.configure(text=text)

    def update_game_statistics(self, moves_played: int = 0, our_moves: int = 0):
        """Update game statistics section"""
        if moves_played > 0:
            text = f"📊 Moves: {moves_played} (Us: {our_moves})"
        else:
            text = "📊 No game active"
        self.game_stats.configure(text=text)

    def update_system_status(self, engine_status: str = "Ready", depth: int = None):
        """Update system status section"""
        text = f"⚙️ Engine: {engine_status}"
        if depth:
            text += f" (D:{depth})"
        self.system_info.configure(text=text)

    def run(self):
        """Run the GUI main loop"""
        try:
            # Center window on screen
            self.root.update_idletasks()
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            x = (self.root.winfo_screenwidth() // 2) - (width // 2)
            y = (self.root.winfo_screenheight() // 2) - (height // 2)
            self.root.geometry(f"{width}x{height}+{x}+{y}")

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

    def start_game_timer(self):
        """Start the game timer (thread-safe)"""
        message = {"type": "timer_start"}
        self.gui_queue.put(message)

    def stop_timers(self):
        """Stop all timers (thread-safe)"""
        message = {"type": "timer_stop"}
        self.gui_queue.put(message)

    def reset_move_timer(self):
        """Reset move timer (thread-safe)"""
        message = {"type": "move_timer_reset"}
        self.gui_queue.put(message)

    def set_activity_status(self, status: str):
        """Set activity status (thread-safe)"""
        message = {"type": "status_activity", "status": status}
        self.gui_queue.put(message)

    def set_connection_status(self, connected: bool, details: str = ""):
        """Set connection status (thread-safe)"""
        message = {
            "type": "status_connection",
            "connected": connected,
            "details": details,
        }
        self.gui_queue.put(message)

    def set_game_statistics(self, moves_played: int = 0, our_moves: int = 0):
        """Set game statistics (thread-safe)"""
        message = {
            "type": "status_game_stats",
            "moves_played": moves_played,
            "our_moves": our_moves,
        }
        self.gui_queue.put(message)

    def set_system_status(self, engine_status: str = "Ready", depth: int = None):
        """Set system status (thread-safe)"""
        message = {
            "type": "status_system",
            "engine_status": engine_status,
            "depth": depth,
        }
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

    def switch_to_tab(self, tab_name: str):
        """Switch to specific tab by name"""
        tab_mapping = {"status": 0, "history": 1, "console": 2}

        if tab_name.lower() in tab_mapping:
            self.notebook.select(tab_mapping[tab_name.lower()])
