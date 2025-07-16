"""Log Panel Widget - Real-time logging and status display"""

import tkinter as tk
from datetime import datetime
from tkinter import ttk
from typing import Dict


class LogPanelWidget(tk.Frame):
    """Panel for displaying real-time logs and status messages"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#2B2B2B", **kwargs)

        # Configuration
        self.max_lines = 500  # Maximum lines to keep
        self.auto_scroll = True

        # Colors for different log levels
        self.level_colors: Dict[str, str] = {
            "trace": "#888888",
            "debug": "#888888",
            "info": "#FFFFFF",
            "success": "#28A745",
            "warning": "#FFC107",
            "error": "#DC3545",
            "critical": "#DC3545",
        }

        self._create_widgets()
        self._setup_layout()

        # Add initial welcome message
        self.add_log("Chess Bot GUI initialized", "success")

    def _create_widgets(self):
        """Create all log panel widgets"""

        # Title with controls
        self.header_frame = tk.Frame(self, bg="#2B2B2B")

        self.title_label = tk.Label(
            self.header_frame,
            text="Activity Log",
            font=("Arial", 14, "bold"),
            fg="#FFFFFF",
            bg="#2B2B2B",
        )

        self.clear_button = tk.Button(
            self.header_frame,
            text="Clear",
            command=self._clear_logs,
            font=("Arial", 9),
            bg="#404040",
            fg="#FFFFFF",
            relief="flat",
            bd=1,
            padx=10,
            pady=2,
        )

        self.auto_scroll_var = tk.BooleanVar(value=True)
        self.auto_scroll_checkbox = tk.Checkbutton(
            self.header_frame,
            text="Auto-scroll",
            variable=self.auto_scroll_var,
            command=self._toggle_auto_scroll,
            font=("Arial", 9),
            fg="#CCCCCC",
            bg="#2B2B2B",
            selectcolor="#404040",
        )

        # Log display area
        self.log_frame = tk.Frame(self, bg="#1A1A1A", relief="solid", bd=1)

        # Text widget with scrollbar
        self.log_text = tk.Text(
            self.log_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg="#1A1A1A",
            fg="#FFFFFF",
            insertbackground="#FFFFFF",
            selectbackground="#404040",
            font=("Consolas", 9),
            relief="flat",
            borderwidth=0,
            padx=8,
            pady=5,
        )

        self.scrollbar = tk.Scrollbar(
            self.log_frame,
            command=self.log_text.yview,
            bg="#404040",
            troughcolor="#2B2B2B",
        )

        self.log_text.configure(yscrollcommand=self.scrollbar.set)

        # Configure text tags for different log levels
        for level, color in self.level_colors.items():
            self.log_text.tag_configure(level, foreground=color)

    def _setup_layout(self):
        """Setup widget layout"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(10, 5))
        self.header_frame.grid_columnconfigure(1, weight=1)

        self.title_label.grid(row=0, column=0, sticky="w")
        self.auto_scroll_checkbox.grid(row=0, column=1, sticky="e", padx=(0, 10))
        self.clear_button.grid(row=0, column=2, sticky="e")

        # Log area
        self.log_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(0, weight=1)

        self.log_text.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

    def add_log(self, message: str, level: str = "info"):
        """Add a log message with timestamp and level"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        level = level.lower()

        # Format the log entry
        log_entry = f"[{timestamp}] {message}\n"

        # Insert the log entry
        self.log_text.configure(state=tk.NORMAL)

        # Insert with appropriate color
        if level in self.level_colors:
            self.log_text.insert(tk.END, log_entry, level)
        else:
            self.log_text.insert(tk.END, log_entry, "info")

        # Manage line count
        self._manage_line_count()

        self.log_text.configure(state=tk.DISABLED)

        # Auto-scroll if enabled
        if self.auto_scroll:
            self.log_text.see(tk.END)

    def _manage_line_count(self):
        """Keep log text under the maximum line limit"""
        lines = self.log_text.get("1.0", tk.END).count("\n")
        if lines > self.max_lines:
            # Remove oldest lines
            lines_to_remove = lines - self.max_lines
            self.log_text.delete("1.0", f"{lines_to_remove + 1}.0")

    def _clear_logs(self):
        """Clear all log messages"""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self.add_log("Log cleared", "info")

    def _toggle_auto_scroll(self):
        """Toggle auto-scroll functionality"""
        self.auto_scroll = self.auto_scroll_var.get()
        if self.auto_scroll:
            self.log_text.see(tk.END)

    def bulk_add_logs(self, logs: list):
        """Add multiple log entries at once (more efficient)"""
        if not logs:
            return

        self.log_text.configure(state=tk.NORMAL)

        for log_data in logs:
            if isinstance(log_data, dict):
                message = log_data.get("message", "")
                level = log_data.get("level", "info")
            else:
                message = str(log_data)
                level = "info"

            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"

            if level.lower() in self.level_colors:
                self.log_text.insert(tk.END, log_entry, level.lower())
            else:
                self.log_text.insert(tk.END, log_entry, "info")

        self._manage_line_count()
        self.log_text.configure(state=tk.DISABLED)

        if self.auto_scroll:
            self.log_text.see(tk.END)
