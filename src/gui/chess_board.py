"""Chess board widget for visual display"""

import math
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
        self.current_arrow = None  # Store current arrow object IDs
        self.last_move = None
        self.suggestion_move = None

        # Colors
        self.light_square_color = "#f0d9b5"
        self.dark_square_color = "#b58863"
        self.last_move_arrow_color = "#ffaa00"  # Orange for last move
        self.suggestion_arrow_color = "#00ff00"  # Green for suggestions

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
        # File labels (a-h) - bottom
        files = "abcdefgh"
        for i, file_char in enumerate(files):
            x = i * self.square_size + self.square_size // 2
            y = self.size + 20  # Slightly more space

            self.canvas.create_text(
                x, y, text=file_char, fill="#cccccc", font=("Arial", 11, "bold")
            )

        # Rank labels (1-8) - left side
        for i in range(8):
            rank = 8 - i if not self.flipped else i + 1
            x = -20  # Slightly more space
            y = i * self.square_size + self.square_size // 2

            self.canvas.create_text(
                x, y, text=str(rank), fill="#cccccc", font=("Arial", 11, "bold")
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

    def _clear_arrow(self):
        """Clear the current arrow"""
        if self.current_arrow:
            for arrow_part in self.current_arrow:
                self.canvas.delete(arrow_part)
            self.current_arrow = None

    def _draw_arrow(self, from_square: int, to_square: int, color: str):
        """Draw an arrow from one square to another"""
        # Clear any existing arrow first
        self._clear_arrow()

        # Get coordinates
        from_row, from_col = self._square_to_coords(from_square)
        to_row, to_col = self._square_to_coords(to_square)

        from_x, from_y = self._coords_to_canvas_pos(from_row, from_col)
        to_x, to_y = self._coords_to_canvas_pos(to_row, to_col)

        # Calculate arrow parameters
        dx = to_x - from_x
        dy = to_y - from_y
        length = math.sqrt(dx * dx + dy * dy)

        if length == 0:
            return

        # Normalize direction
        unit_x = dx / length
        unit_y = dy / length

        # Adjust start and end points to avoid overlapping pieces
        margin = self.square_size * 0.25
        start_x = from_x + unit_x * margin
        start_y = from_y + unit_y * margin
        end_x = to_x - unit_x * margin
        end_y = to_y - unit_y * margin

        # Arrow head size
        head_length = self.square_size * 0.3
        head_width = self.square_size * 0.15

        # Calculate arrowhead points
        head_back_x = end_x - unit_x * head_length
        head_back_y = end_y - unit_y * head_length

        # Perpendicular vector for arrowhead width
        perp_x = -unit_y * head_width
        perp_y = unit_x * head_width

        # Arrow shaft (thick line)
        shaft_width = 6
        arrow_parts = []

        # Draw arrow shaft
        shaft_id = self.canvas.create_line(
            start_x,
            start_y,
            head_back_x,
            head_back_y,
            fill=color,
            width=shaft_width,
            capstyle=tk.ROUND,
            tags="arrow_shaft",
        )
        arrow_parts.append(shaft_id)

        # Draw arrowhead (triangle)
        head_points = [
            end_x,
            end_y,  # Arrow tip
            head_back_x + perp_x,
            head_back_y + perp_y,  # Left point
            head_back_x - perp_x,
            head_back_y - perp_y,  # Right point
        ]

        head_id = self.canvas.create_polygon(
            head_points, fill=color, outline=color, tags="arrow_head"
        )
        arrow_parts.append(head_id)

        self.current_arrow = arrow_parts

    def update_position(
        self, board: chess.Board, highlight_move: Optional[chess.Move] = None
    ):
        """Update the board position"""
        self.board_state = board.copy()

        # Store the last move
        if highlight_move:
            self.last_move = highlight_move

        # Redraw pieces
        self._draw_pieces()

        # Show the appropriate arrow (prioritize suggestion over last move)
        if self.suggestion_move:
            self._draw_arrow(
                self.suggestion_move.from_square,
                self.suggestion_move.to_square,
                self.suggestion_arrow_color,
            )
        elif self.last_move:
            self._draw_arrow(
                self.last_move.from_square,
                self.last_move.to_square,
                self.last_move_arrow_color,
            )

    def show_suggestion(self, move: chess.Move):
        """Show a move suggestion with an arrow"""
        self.suggestion_move = move

        # Draw suggestion arrow (this will clear any existing arrow)
        self._draw_arrow(move.from_square, move.to_square, self.suggestion_arrow_color)

    def clear_suggestion(self):
        """Clear move suggestion"""
        self.suggestion_move = None

        # Show last move arrow if it exists, otherwise clear arrow
        if self.last_move:
            self._draw_arrow(
                self.last_move.from_square,
                self.last_move.to_square,
                self.last_move_arrow_color,
            )
        else:
            self._clear_arrow()

    def set_perspective(self, white_at_bottom: bool = True):
        """Set board perspective (True = white at bottom, False = black at bottom)"""
        if self.flipped != (not white_at_bottom):
            self.flipped = not white_at_bottom
            self._create_board()
            self._draw_pieces()

            # Redraw arrow if one exists
            if self.suggestion_move:
                self._draw_arrow(
                    self.suggestion_move.from_square,
                    self.suggestion_move.to_square,
                    self.suggestion_arrow_color,
                )
            elif self.last_move:
                self._draw_arrow(
                    self.last_move.from_square,
                    self.last_move.to_square,
                    self.last_move_arrow_color,
                )

    def get_canvas(self) -> Canvas:
        """Get the underlying canvas widget"""
        return self.canvas
