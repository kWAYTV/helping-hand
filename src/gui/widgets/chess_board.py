"""Chess Board Widget - Visual chess board display"""

import tkinter as tk
from typing import Optional

import chess


class ChessBoardWidget(tk.Frame):
    """Professional chess board widget with position display and move arrows"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#2B2B2B", **kwargs)

        # Board configuration
        self.base_size = 400  # Base board size
        self.orientation = "white"  # "white" or "black"

        # Colors
        self.light_square_color = "#F0D9B5"
        self.dark_square_color = "#B58863"
        self.suggestion_color = "#00FF00"
        self.last_move_color = "#FFFF7F"

        # State
        self.current_board = chess.Board()
        self.last_move = None
        self.suggestion_move = None

        # Create the canvas
        self._create_canvas()
        self._draw_initial_board()

        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Bind resize events
        self.bind("<Configure>", self._on_resize)

    def _create_canvas(self):
        """Create the main canvas for the chess board"""
        self.canvas = tk.Canvas(
            self, bg="#2B2B2B", highlightthickness=0, relief="solid", borderwidth=1
        )
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Bind canvas resize
        self.canvas.bind("<Configure>", self._on_canvas_resize)

    def _on_resize(self, event):
        """Handle widget resize"""
        pass  # Canvas handles its own resize

    def _on_canvas_resize(self, event):
        """Handle canvas resize and redraw board"""
        # Calculate new board size based on available space
        available_width = event.width - 20  # Padding
        available_height = event.height - 20  # Padding

        # Keep it square
        new_size = min(available_width, available_height, 500)  # Max 500px
        if new_size > 100:  # Minimum size
            self.board_size = new_size
            self.square_size = self.board_size // 8
            self._redraw_all()

    def _draw_initial_board(self):
        """Draw initial empty board"""
        self.board_size = self.base_size
        self.square_size = self.board_size // 8
        self._redraw_all()

    def _redraw_all(self):
        """Redraw everything on the board"""
        self.canvas.delete("all")
        self._draw_board()
        self._draw_coordinates()
        self._draw_pieces()
        if self.suggestion_move:
            self._draw_suggestion_arrow()

    def _draw_board(self):
        """Draw the chess board squares"""
        start_x = (self.canvas.winfo_width() - self.board_size) // 2
        start_y = (self.canvas.winfo_height() - self.board_size) // 2

        # Ensure we have valid canvas dimensions
        if start_x < 0:
            start_x = 10
        if start_y < 0:
            start_y = 10

        for rank in range(8):
            for file in range(8):
                x1 = start_x + file * self.square_size
                y1 = start_y + rank * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size

                # Determine square color
                is_light = (rank + file) % 2 == 0
                color = self.light_square_color if is_light else self.dark_square_color

                # Highlight last move
                if self.last_move and self._is_square_in_move(
                    rank, file, self.last_move
                ):
                    color = self.last_move_color

                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=color, outline="#8B4513", width=1, tags="board"
                )

    def _draw_coordinates(self):
        """Draw file and rank coordinates around the board"""
        start_x = (self.canvas.winfo_width() - self.board_size) // 2
        start_y = (self.canvas.winfo_height() - self.board_size) // 2

        if start_x < 0:
            start_x = 10
        if start_y < 0:
            start_y = 10

        files = "abcdefgh" if self.orientation == "white" else "hgfedcba"
        ranks = "87654321" if self.orientation == "white" else "12345678"

        font_size = max(8, self.square_size // 8)

        # File letters (bottom)
        for i, file_letter in enumerate(files):
            x = start_x + i * self.square_size + self.square_size // 2
            y = start_y + self.board_size + 15
            self.canvas.create_text(
                x,
                y,
                text=file_letter,
                fill="#CCCCCC",
                font=("Arial", font_size, "bold"),
                tags="coordinates",
            )

        # Rank numbers (left side)
        for i, rank_number in enumerate(ranks):
            x = start_x - 15
            y = start_y + i * self.square_size + self.square_size // 2
            self.canvas.create_text(
                x,
                y,
                text=rank_number,
                fill="#CCCCCC",
                font=("Arial", font_size, "bold"),
                tags="coordinates",
            )

    def _draw_pieces(self):
        """Draw chess pieces on the board"""
        start_x = (self.canvas.winfo_width() - self.board_size) // 2
        start_y = (self.canvas.winfo_height() - self.board_size) // 2

        if start_x < 0:
            start_x = 10
        if start_y < 0:
            start_y = 10

        piece_symbols = {
            chess.PAWN: ("♟", "♙"),
            chess.ROOK: ("♜", "♖"),
            chess.KNIGHT: ("♞", "♘"),
            chess.BISHOP: ("♝", "♗"),
            chess.QUEEN: ("♛", "♕"),
            chess.KING: ("♚", "♔"),
        }

        font_size = max(12, int(self.square_size * 0.6))

        for square in chess.SQUARES:
            piece = self.current_board.piece_at(square)
            if piece:
                file_idx = chess.square_file(square)
                rank_idx = chess.square_rank(square)

                # Adjust for board orientation
                if self.orientation == "white":
                    x = start_x + file_idx * self.square_size + self.square_size // 2
                    y = (
                        start_y
                        + (7 - rank_idx) * self.square_size
                        + self.square_size // 2
                    )
                else:
                    x = (
                        start_x
                        + (7 - file_idx) * self.square_size
                        + self.square_size // 2
                    )
                    y = start_y + rank_idx * self.square_size + self.square_size // 2

                # Select piece symbol (white pieces = True, black pieces = False)
                symbol = piece_symbols[piece.piece_type][1 if piece.color else 0]

                self.canvas.create_text(
                    x,
                    y,
                    text=symbol,
                    fill="#FFFFFF" if piece.color else "#000000",
                    font=("Arial", font_size, "bold"),
                    tags="pieces",
                )

    def _draw_suggestion_arrow(self):
        """Draw an arrow for the engine suggestion"""
        if not self.suggestion_move:
            return

        start_x = (self.canvas.winfo_width() - self.board_size) // 2
        start_y = (self.canvas.winfo_height() - self.board_size) // 2

        if start_x < 0:
            start_x = 10
        if start_y < 0:
            start_y = 10

        from_square = self.suggestion_move.from_square
        to_square = self.suggestion_move.to_square

        from_x, from_y = self._square_to_canvas_coords(from_square, start_x, start_y)
        to_x, to_y = self._square_to_canvas_coords(to_square, start_x, start_y)

        # Draw arrow line
        arrow_width = max(2, self.square_size // 20)
        self.canvas.create_line(
            from_x,
            from_y,
            to_x,
            to_y,
            fill=self.suggestion_color,
            width=arrow_width,
            arrow=tk.LAST,
            arrowshape=(16, 20, 6),
            tags="suggestion",
        )

        # Draw source circle
        circle_radius = max(4, self.square_size // 15)
        self.canvas.create_oval(
            from_x - circle_radius,
            from_y - circle_radius,
            from_x + circle_radius,
            from_y + circle_radius,
            fill=self.suggestion_color,
            outline="",
            tags="suggestion",
        )

    def _square_to_canvas_coords(self, square, start_x, start_y):
        """Convert chess square to canvas coordinates"""
        file_idx = chess.square_file(square)
        rank_idx = chess.square_rank(square)

        if self.orientation == "white":
            x = start_x + file_idx * self.square_size + self.square_size // 2
            y = start_y + (7 - rank_idx) * self.square_size + self.square_size // 2
        else:
            x = start_x + (7 - file_idx) * self.square_size + self.square_size // 2
            y = start_y + rank_idx * self.square_size + self.square_size // 2

        return x, y

    def _is_square_in_move(self, rank, file, move):
        """Check if a square is part of a move (for highlighting)"""
        if self.orientation == "white":
            square = chess.square(file, 7 - rank)
        else:
            square = chess.square(7 - file, rank)

        return square == move.from_square or square == move.to_square

    def update_position(
        self, board: chess.Board, last_move: Optional[chess.Move] = None
    ):
        """Update the board position"""
        self.current_board = board.copy()
        self.last_move = last_move
        self._redraw_all()

    def show_suggestion(self, move: chess.Move):
        """Show an engine suggestion with an arrow"""
        self.suggestion_move = move
        self._draw_suggestion_arrow()

    def clear_suggestion(self):
        """Clear the suggestion arrow"""
        self.suggestion_move = None
        self.canvas.delete("suggestion")

    def set_orientation(self, color: str):
        """Set board orientation (white/black)"""
        self.orientation = color.lower()
        self._redraw_all()
