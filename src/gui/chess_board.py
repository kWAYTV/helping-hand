"""Chess board widget for visual display"""

import tkinter as tk
from tkinter import Canvas
from typing import Dict, Optional, Tuple

import chess


class ChessBoardWidget:
    """A visual chess board widget using tkinter Canvas"""

    # Unicode chess pieces
    PIECE_SYMBOLS = {
        "P": "♙",
        "R": "♖",
        "N": "♘",
        "B": "♗",
        "Q": "♕",
        "K": "♔",  # White pieces
        "p": "♟",
        "r": "♜",
        "n": "♞",
        "b": "♝",
        "q": "♛",
        "k": "♚",  # Black pieces
    }

    def __init__(self, parent, size: int = 400):
        self.parent = parent
        self.size = size
        self.square_size = size // 8
        self.board_state = chess.Board()
        self.flipped = False  # False = white at bottom, True = black at bottom
        self.highlighted_squares = set()
        self.suggestion_move = None

        # Colors
        self.light_square_color = "#f0d9b5"
        self.dark_square_color = "#b58863"
        self.highlight_color = "#ffff00"
        self.suggestion_color = "#00ff00"
        self.last_move_color = "#ffdd44"

        # Create canvas
        self.canvas = Canvas(
            parent,
            width=size,
            height=size,
            bg="#2b2b2b",
            highlightthickness=2,
            highlightbackground="#555555",
        )

        # Store piece objects for efficient updates
        self.piece_objects = {}
        self.square_objects = {}
        self.highlight_objects = {}

        self._create_board()
        self._draw_pieces()

    def pack(self, **kwargs):
        """Pack the canvas"""
        self.canvas.pack(**kwargs)

    def _create_board(self):
        """Create the chess board squares"""
        for row in range(8):
            for col in range(8):
                x1 = col * self.square_size
                y1 = row * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size

                # Determine square color
                is_light = (row + col) % 2 == 0
                color = self.light_square_color if is_light else self.dark_square_color

                # Create square
                square_id = self.canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=color,
                    outline=color,
                    tags=f"square_{row}_{col}",
                )

                self.square_objects[(row, col)] = square_id

        # Add coordinate labels
        self._add_coordinates()

    def _add_coordinates(self):
        """Add coordinate labels to the board"""
        # File labels (a-h)
        files = "abcdefgh"
        for i, file_char in enumerate(files):
            x = i * self.square_size + self.square_size // 2
            y = self.size + 15

            self.canvas.create_text(
                x, y, text=file_char, fill="#ffffff", font=("Arial", 10, "bold")
            )

        # Rank labels (1-8)
        for i in range(8):
            rank = 8 - i if not self.flipped else i + 1
            x = -15
            y = i * self.square_size + self.square_size // 2

            self.canvas.create_text(
                x, y, text=str(rank), fill="#ffffff", font=("Arial", 10, "bold")
            )

    def _square_to_coords(self, square: int) -> Tuple[int, int]:
        """Convert chess square index to canvas coordinates"""
        file = square % 8
        rank = square // 8

        if self.flipped:
            canvas_col = 7 - file
            canvas_row = rank
        else:
            canvas_col = file
            canvas_row = 7 - rank

        return canvas_row, canvas_col

    def _coords_to_canvas_pos(self, row: int, col: int) -> Tuple[int, int]:
        """Convert grid coordinates to canvas pixel position"""
        x = col * self.square_size + self.square_size // 2
        y = row * self.square_size + self.square_size // 2
        return x, y

    def _draw_pieces(self):
        """Draw all pieces on the board"""
        # Clear existing pieces
        for piece_id in self.piece_objects.values():
            self.canvas.delete(piece_id)
        self.piece_objects.clear()

        # Draw current pieces
        for square in range(64):
            piece = self.board_state.piece_at(square)
            if piece:
                self._draw_piece_at_square(square, piece)

    def _draw_piece_at_square(self, square: int, piece: chess.Piece):
        """Draw a piece at the specified square"""
        row, col = self._square_to_coords(square)
        x, y = self._coords_to_canvas_pos(row, col)

        # Get piece symbol
        piece_char = piece.symbol()
        piece_unicode = self.PIECE_SYMBOLS.get(piece_char, piece_char)

        # Choose color
        color = "#ffffff" if piece.color == chess.WHITE else "#000000"

        # Create text object
        piece_id = self.canvas.create_text(
            x,
            y,
            text=piece_unicode,
            fill=color,
            font=("Arial", int(self.square_size * 0.6), "normal"),
            tags=f"piece_{square}",
        )

        self.piece_objects[square] = piece_id

    def _clear_highlights(self):
        """Clear all square highlights"""
        for highlight_id in self.highlight_objects.values():
            self.canvas.delete(highlight_id)
        self.highlight_objects.clear()
        self.highlighted_squares.clear()

    def _highlight_square(self, square: int, color: str):
        """Highlight a specific square"""
        row, col = self._square_to_coords(square)
        x1 = col * self.square_size
        y1 = row * self.square_size
        x2 = x1 + self.square_size
        y2 = y1 + self.square_size

        # Create highlight rectangle
        highlight_id = self.canvas.create_rectangle(
            x1, y1, x2, y2, fill=color, stipple="gray50", tags=f"highlight_{square}"
        )

        self.highlight_objects[square] = highlight_id
        self.highlighted_squares.add(square)

    def _highlight_move(self, move: chess.Move, color: str):
        """Highlight a move (from and to squares)"""
        self._highlight_square(move.from_square, color)
        self._highlight_square(move.to_square, color)

    def update_position(
        self, board: chess.Board, highlight_move: Optional[chess.Move] = None
    ):
        """Update the board position"""
        self.board_state = board.copy()

        # Clear previous highlights
        self._clear_highlights()

        # Redraw pieces
        self._draw_pieces()

        # Highlight last move if provided
        if highlight_move:
            self._highlight_move(highlight_move, self.last_move_color)

        # Show suggestion if exists
        if self.suggestion_move:
            self._highlight_move(self.suggestion_move, self.suggestion_color)

    def show_suggestion(self, move: chess.Move):
        """Show a move suggestion"""
        self.suggestion_move = move

        # Clear previous suggestion highlights
        if hasattr(self, "_suggestion_highlights"):
            for highlight_id in self._suggestion_highlights:
                self.canvas.delete(highlight_id)

        # Highlight suggestion move
        self._highlight_move(move, self.suggestion_color)

    def clear_suggestion(self):
        """Clear move suggestion"""
        self.suggestion_move = None
        # Redraw board to remove suggestion highlights
        self.update_position(self.board_state)

    def set_perspective(self, white_at_bottom: bool = True):
        """Set board perspective (True = white at bottom, False = black at bottom)"""
        if self.flipped != (not white_at_bottom):
            self.flipped = not white_at_bottom
            self._create_board()
            self._draw_pieces()

    def highlight_squares(self, squares: list, color: str = None):
        """Highlight multiple squares"""
        if color is None:
            color = self.highlight_color

        for square in squares:
            self._highlight_square(square, color)

    def get_canvas(self) -> Canvas:
        """Get the underlying canvas widget"""
        return self.canvas
