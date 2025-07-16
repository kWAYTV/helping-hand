"""Game Info Widget - Current game state and engine information"""

import tkinter as tk
from tkinter import ttk
from typing import Optional

import chess


class GameInfoWidget(tk.Frame):
    """Widget displaying current game information and engine suggestions"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#2B2B2B", **kwargs)

        # State
        self.current_move = None
        self.our_color = "white"
        self.game_active = False

        self._create_widgets()
        self._setup_layout()

    def _create_widgets(self):
        """Create all info widgets"""

        # Title
        self.title_label = tk.Label(
            self,
            text="Game Information",
            font=("Arial", 14, "bold"),
            fg="#FFFFFF",
            bg="#2B2B2B",
        )

        # Game status frame
        self.status_frame = tk.Frame(self, bg="#1A1A1A", relief="solid", bd=1)

        self.color_label = tk.Label(
            self.status_frame,
            text="Playing as: Unknown",
            font=("Arial", 10),
            fg="#CCCCCC",
            bg="#1A1A1A",
        )

        self.turn_label = tk.Label(
            self.status_frame,
            text="Turn: White to move",
            font=("Arial", 10),
            fg="#CCCCCC",
            bg="#1A1A1A",
        )

        self.move_number_label = tk.Label(
            self.status_frame,
            text="Move: 1",
            font=("Arial", 10),
            fg="#CCCCCC",
            bg="#1A1A1A",
        )

        # Engine suggestion frame
        self.engine_frame = tk.Frame(self, bg="#1A1A1A", relief="solid", bd=1)

        self.engine_title = tk.Label(
            self.engine_frame,
            text="Engine Suggestion",
            font=("Arial", 12, "bold"),
            fg="#FFFFFF",
            bg="#1A1A1A",
        )

        self.suggestion_label = tk.Label(
            self.engine_frame,
            text="No suggestion",
            font=("Arial", 11, "bold"),
            fg="#888888",
            bg="#1A1A1A",
        )

        self.evaluation_label = tk.Label(
            self.engine_frame,
            text="Evaluation: N/A",
            font=("Arial", 9),
            fg="#CCCCCC",
            bg="#1A1A1A",
        )

        self.depth_label = tk.Label(
            self.engine_frame,
            text="Depth: N/A",
            font=("Arial", 9),
            fg="#CCCCCC",
            bg="#1A1A1A",
        )

    def _setup_layout(self):
        """Setup widget layout - vertical for side panel placement"""
        self.grid_columnconfigure(0, weight=1)

        # Title
        self.title_label.grid(row=0, column=0, pady=(10, 10), sticky="ew")

        # Game status
        self.status_frame.grid(row=1, column=0, pady=(0, 10), padx=5, sticky="ew")
        self.status_frame.grid_columnconfigure(0, weight=1)

        self.color_label.grid(row=0, column=0, pady=5, padx=10, sticky="w")
        self.turn_label.grid(row=1, column=0, pady=2, padx=10, sticky="w")
        self.move_number_label.grid(row=2, column=0, pady=5, padx=10, sticky="w")

        # Engine info
        self.engine_frame.grid(row=2, column=0, pady=(0, 10), padx=5, sticky="ew")
        self.engine_frame.grid_columnconfigure(0, weight=1)

        self.engine_title.grid(row=0, column=0, pady=(10, 8), sticky="ew")
        self.suggestion_label.grid(row=1, column=0, pady=2, padx=10, sticky="w")
        self.evaluation_label.grid(row=2, column=0, pady=2, padx=10, sticky="w")
        self.depth_label.grid(row=3, column=0, pady=(2, 10), padx=10, sticky="w")

    def update_info(self, info: dict):
        """Update game information"""

        # Update color
        if "our_color" in info:
            color = info["our_color"]
            self.our_color = color
            color_text = (
                "White" if color.lower() == "white" or color == "W" else "Black"
            )
            self.color_label.configure(text=f"Playing as: {color_text}")

        # Update turn
        if "turn" in info:
            turn = info["turn"]
            turn_text = "White to move" if turn else "Black to move"
            self.turn_label.configure(text=f"Turn: {turn_text}")

        # Update move number
        if "move_number" in info:
            move_num = info["move_number"]
            self.move_number_label.configure(text=f"Move: {move_num}")

        # Update game status
        if "game_active" in info:
            self.game_active = info["game_active"]

    def update_suggestion(self, move: chess.Move, evaluation: dict = None):
        """Update engine suggestion display"""
        if move:
            # Format move nicely
            move_str = str(move)
            from_square = move_str[:2].upper()
            to_square = move_str[2:4].upper()

            # Check for promotion
            if len(move_str) > 4:
                promotion = move_str[4:].upper()
                move_display = f"{from_square} → {to_square}={promotion}"
            else:
                move_display = f"{from_square} → {to_square}"

            self.suggestion_label.configure(text=move_display, fg="#00AA00")

            # Update evaluation if provided
            if evaluation:
                if "score" in evaluation and evaluation["score"]:
                    score = evaluation["score"]
                    if hasattr(score, "relative") and score.relative is not None:
                        score_val = score.relative.score(mate_score=10000) / 100.0
                        self.evaluation_label.configure(
                            text=f"Evaluation: {score_val:+.2f}"
                        )
                    elif hasattr(score, "white") and score.white is not None:
                        score_val = score.white().score(mate_score=10000) / 100.0
                        self.evaluation_label.configure(
                            text=f"Evaluation: {score_val:+.2f}"
                        )
                    else:
                        self.evaluation_label.configure(text="Evaluation: N/A")
                else:
                    self.evaluation_label.configure(text="Evaluation: N/A")

                if "depth" in evaluation:
                    depth = evaluation["depth"]
                    self.depth_label.configure(text=f"Depth: {depth}")
            else:
                self.evaluation_label.configure(text="Evaluation: N/A")
                self.depth_label.configure(text="Depth: N/A")
        else:
            self.suggestion_label.configure(text="No suggestion", fg="#888888")
            self.evaluation_label.configure(text="Evaluation: N/A")
            self.depth_label.configure(text="Depth: N/A")

    def clear_suggestion(self):
        """Clear the current suggestion"""
        self.update_suggestion(None)
