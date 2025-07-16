"""Move History Widget - Scrollable list of game moves"""

import tkinter as tk
from tkinter import ttk
from typing import List, Optional

import chess


class MoveHistoryWidget(tk.Frame):
    """Widget displaying scrollable move history"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#2B2B2B", **kwargs)

        # State
        self.moves: List[tuple] = []  # [(move_number, white_move, black_move), ...]
        self.current_move_number = 0

        self._create_widgets()
        self._setup_layout()

    def _create_widgets(self):
        """Create all history widgets"""

        # Title
        self.title_label = tk.Label(
            self,
            text="Move History",
            font=("Arial", 14, "bold"),
            fg="#FFFFFF",
            bg="#2B2B2B",
        )

        # Create frame for treeview and scrollbar
        self.tree_frame = tk.Frame(self, bg="#1A1A1A", relief="solid", bd=1)

        # Create treeview for moves
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=("move_num", "white", "black"),
            show="headings",
            height=12,
        )

        # Configure columns
        self.tree.heading("move_num", text="#")
        self.tree.heading("white", text="White")
        self.tree.heading("black", text="Black")

        self.tree.column("move_num", width=40, anchor="center")
        self.tree.column("white", width=80, anchor="center")
        self.tree.column("black", width=80, anchor="center")

        # Configure treeview styling
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background="#1A1A1A",
            foreground="#CCCCCC",
            fieldbackground="#1A1A1A",
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background="#333333",
            foreground="#FFFFFF",
            borderwidth=1,
            relief="solid",
        )
        style.map("Treeview", background=[("selected", "#4A4A4A")])

        # Create scrollbar
        self.scrollbar = ttk.Scrollbar(
            self.tree_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        # Status label
        self.status_label = tk.Label(
            self,
            text="No moves yet",
            font=("Arial", 9),
            fg="#888888",
            bg="#2B2B2B",
        )

    def _setup_layout(self):
        """Setup widget layout"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Title
        self.title_label.grid(row=0, column=0, pady=(10, 5), sticky="ew")

        # Tree frame
        self.tree_frame.grid(row=1, column=0, pady=(0, 5), padx=5, sticky="nsew")
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)

        # Tree and scrollbar
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # Status
        self.status_label.grid(row=2, column=0, pady=(0, 10), sticky="ew")

    def add_move(self, move: chess.Move, move_number: int, is_white: bool):
        """Add a move to the history"""
        move_str = str(move)

        # Calculate the pair number (each pair represents one full move)
        pair_number = (move_number + 1) // 2

        if is_white:
            # White move - start new pair or update existing incomplete pair
            if pair_number > len(self.moves):
                # New pair
                self.moves.append((pair_number, move_str, ""))
            else:
                # Update existing pair (shouldn't happen normally)
                self.moves[pair_number - 1] = (
                    pair_number,
                    move_str,
                    self.moves[pair_number - 1][2],
                )
        else:
            # Black move - complete the pair
            if pair_number > len(self.moves):
                # This shouldn't happen (black move without white move)
                self.moves.append((pair_number, "", move_str))
            else:
                # Complete the pair
                white_move = (
                    self.moves[pair_number - 1][1]
                    if pair_number <= len(self.moves)
                    else ""
                )
                self.moves[pair_number - 1] = (pair_number, white_move, move_str)

        self.current_move_number = move_number
        self._refresh_display()

    def _refresh_display(self):
        """Refresh the treeview display"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add all moves
        for move_num, white_move, black_move in self.moves:
            self.tree.insert(
                "",
                "end",
                values=(move_num, white_move or "-", black_move or "-"),
            )

        # Auto-scroll to bottom
        if self.moves:
            last_item = self.tree.get_children()[-1]
            self.tree.see(last_item)

        # Update status
        total_moves = sum(1 for _, white, black in self.moves if white) + sum(
            1 for _, white, black in self.moves if black
        )
        if total_moves == 0:
            self.status_label.configure(text="No moves yet")
        else:
            self.status_label.configure(text=f"Total moves: {total_moves}")

    def clear_history(self):
        """Clear all move history"""
        self.moves.clear()
        self.current_move_number = 0
        self._refresh_display()

    def get_move_count(self) -> int:
        """Get total number of moves"""
        return sum(1 for _, white, black in self.moves if white) + sum(
            1 for _, white, black in self.moves if black
        )
