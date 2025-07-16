"""Move history panel for displaying game moves"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List


class MoveHistoryPanel:
    """Panel showing move history in a chess-website style"""

    def __init__(self, parent):
        self.parent = parent
        self.moves = []  # List of move dictionaries

        # Create main frame
        self.frame = ttk.LabelFrame(parent, text="Move History", padding=5)

        # Create move display
        self._create_widgets()
        self._setup_layout()

    def _create_widgets(self):
        """Create move history widgets"""
        # Scrolled text for moves
        self.moves_frame = tk.Frame(self.frame, bg="#1e1e1e")

        # Canvas and scrollbar for custom move display
        self.canvas = tk.Canvas(
            self.moves_frame, bg="#1e1e1e", height=120, highlightthickness=0
        )

        self.scrollbar = ttk.Scrollbar(
            self.moves_frame, orient="vertical", command=self.canvas.yview
        )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Frame inside canvas for moves
        self.moves_content = tk.Frame(self.canvas, bg="#1e1e1e")
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.moves_content, anchor="nw"
        )

        # Bind canvas resize
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.moves_content.bind("<Configure>", self._on_frame_configure)

    def _setup_layout(self):
        """Setup layout"""
        # Pack canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def _on_canvas_configure(self, event):
        """Handle canvas resize"""
        # Update scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        # Update content frame width
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def _on_frame_configure(self, event):
        """Handle frame resize"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def grid(self, **kwargs):
        """Grid the move history panel"""
        self.frame.grid(**kwargs)
        self.moves_frame.pack(fill="both", expand=True)

    def add_move(self, move_data: Dict):
        """Add a move to the history"""
        self.moves.append(move_data)
        self._update_display()

    def clear_moves(self):
        """Clear all moves"""
        self.moves.clear()
        self._update_display()

    def _update_display(self):
        """Update the move display"""
        # Clear existing widgets
        for widget in self.moves_content.winfo_children():
            widget.destroy()

        if not self.moves:
            # Show "No moves" message
            no_moves_label = tk.Label(
                self.moves_content,
                text="No moves yet",
                fg="#888888",
                bg="#1e1e1e",
                font=("Arial", 10, "italic"),
            )
            no_moves_label.pack(pady=10)
            return

        # Group moves by pairs (white, black)
        move_pairs = []
        current_pair = {}

        for move in self.moves:
            move_num = (move["move_number"] + 1) // 2  # Convert to move pair number

            if move["move_number"] % 2 == 1:  # White move (odd numbers)
                current_pair = {"number": move_num, "white": move, "black": None}
                move_pairs.append(current_pair)
            else:  # Black move (even numbers)
                if move_pairs and move_pairs[-1]["number"] == move_num:
                    move_pairs[-1]["black"] = move

        # Display move pairs
        for i, pair in enumerate(move_pairs):
            self._create_move_pair_widget(pair, i)

        # Update scroll region
        self.moves_content.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        # Scroll to bottom
        self.canvas.yview_moveto(1.0)

    def _create_move_pair_widget(self, pair: Dict, index: int):
        """Create widget for a move pair"""
        # Main frame for this move pair
        pair_frame = tk.Frame(self.moves_content, bg="#1e1e1e")
        pair_frame.pack(fill="x", padx=2, pady=1)

        # Move number
        number_label = tk.Label(
            pair_frame,
            text=f"{pair['number']}.",
            fg="#ffffff",
            bg="#1e1e1e",
            font=("Arial", 10, "bold"),
            width=3,
            anchor="w",
        )
        number_label.pack(side="left", padx=(0, 5))

        # White move
        white_move = pair["white"]
        if white_move:
            white_color = "#ffff88" if white_move["player"] == "us" else "#ffffff"
            white_label = tk.Label(
                pair_frame,
                text=white_move["move"],
                fg=white_color,
                bg="#1e1e1e",
                font=("Arial", 10),
                width=8,
                anchor="w",
            )
            white_label.pack(side="left", padx=(0, 10))

        # Black move
        black_move = pair["black"]
        if black_move:
            black_color = "#ffff88" if black_move["player"] == "us" else "#ffffff"
            black_label = tk.Label(
                pair_frame,
                text=black_move["move"],
                fg=black_color,
                bg="#1e1e1e",
                font=("Arial", 10),
                width=8,
                anchor="w",
            )
            black_label.pack(side="left")

    def highlight_last_move(self):
        """Highlight the last move"""
        # This could be implemented to highlight the most recent move
        pass

    def get_move_count(self) -> int:
        """Get total number of moves"""
        return len(self.moves)
