"""Status panel for displaying game information"""

import tkinter as tk
from tkinter import ttk
from typing import Optional


class StatusPanel:
    """Panel showing current game status and bot information"""

    def __init__(self, parent):
        self.parent = parent

        # Create main frame
        self.frame = ttk.Frame(parent)

        # Status variables
        self.game_status_var = tk.StringVar(value="Waiting for game...")
        self.bot_mode_var = tk.StringVar(value="Unknown")
        self.our_color_var = tk.StringVar(value="Unknown")
        self.engine_depth_var = tk.StringVar(value="Unknown")
        self.suggestion_var = tk.StringVar(value="No suggestion")
        self.evaluation_var = tk.StringVar(value="")

        self._create_widgets()
        self._setup_layout()

    def _create_widgets(self):
        """Create status widgets"""
        # Game status
        self.status_label = ttk.Label(self.frame, text="Game Status:")
        self.status_value = ttk.Label(
            self.frame, textvariable=self.game_status_var, font=("Arial", 10, "bold")
        )

        # Bot mode
        self.mode_label = ttk.Label(self.frame, text="Bot Mode:")
        self.mode_value = ttk.Label(
            self.frame, textvariable=self.bot_mode_var, font=("Arial", 10, "bold")
        )

        # Our color
        self.color_label = ttk.Label(self.frame, text="Playing as:")
        self.color_value = ttk.Label(
            self.frame, textvariable=self.our_color_var, font=("Arial", 10, "bold")
        )

        # Engine depth
        self.depth_label = ttk.Label(self.frame, text="Engine Depth:")
        self.depth_value = ttk.Label(
            self.frame, textvariable=self.engine_depth_var, font=("Arial", 10)
        )

        # Current suggestion
        self.suggestion_label = ttk.Label(self.frame, text="Current Suggestion:")
        self.suggestion_value = ttk.Label(
            self.frame,
            textvariable=self.suggestion_var,
            font=("Arial", 12, "bold"),
            foreground="#48ca1a",  # Better green for dark theme
        )

        # Evaluation
        self.evaluation_value = ttk.Label(
            self.frame,
            textvariable=self.evaluation_var,
            font=("Arial", 9),
            foreground="#888888",
        )

    def _setup_layout(self):
        """Setup widget layout"""
        # Configure grid weights
        self.frame.grid_columnconfigure(1, weight=1)

        # Layout widgets
        row = 0

        # Game status
        self.status_label.grid(row=row, column=0, sticky="w", padx=(0, 10))
        self.status_value.grid(row=row, column=1, sticky="w")
        row += 1

        # Bot mode
        self.mode_label.grid(row=row, column=0, sticky="w", padx=(0, 10))
        self.mode_value.grid(row=row, column=1, sticky="w")
        row += 1

        # Our color
        self.color_label.grid(row=row, column=0, sticky="w", padx=(0, 10))
        self.color_value.grid(row=row, column=1, sticky="w")
        row += 1

        # Engine depth
        self.depth_label.grid(row=row, column=0, sticky="w", padx=(0, 10))
        self.depth_value.grid(row=row, column=1, sticky="w")
        row += 1

        # Separator
        separator = ttk.Separator(self.frame, orient="horizontal")
        separator.grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
        row += 1

        # Current suggestion
        self.suggestion_label.grid(row=row, column=0, columnspan=2, sticky="w")
        row += 1

        self.suggestion_value.grid(row=row, column=0, columnspan=2, sticky="w")
        row += 1

        self.evaluation_value.grid(row=row, column=0, columnspan=2, sticky="w")

    def grid(self, **kwargs):
        """Grid the status panel"""
        self.frame.grid(**kwargs)

    def update_status(self, status: str):
        """Update game status"""
        self.game_status_var.set(status)

    def update_bot_mode(self, mode: str):
        """Update bot mode (AutoPlay/Suggestion)"""
        self.bot_mode_var.set(mode)

    def update_our_color(self, color: str):
        """Update our playing color"""
        self.our_color_var.set(color)

    def update_engine_depth(self, depth: int):
        """Update engine depth"""
        self.engine_depth_var.set(str(depth))

    def update_suggestion(self, move: str, evaluation: Optional[str] = None):
        """Update current move suggestion"""
        self.suggestion_var.set(move)
        if evaluation:
            self.evaluation_var.set(f"Eval: {evaluation}")
        else:
            self.evaluation_var.set("")

    def clear_suggestion(self):
        """Clear current suggestion"""
        self.suggestion_var.set("No suggestion")
        self.evaluation_var.set("")
