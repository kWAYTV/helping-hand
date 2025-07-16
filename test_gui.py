"""
Test GUI layout and responsiveness
"""

import tkinter as tk

import chess

from src.gui.main_window import ChessBotGUI


def test_move_history():
    """Test the move history functionality"""
    gui = ChessBotGUI()

    # Add some test moves
    test_moves = [
        (chess.Move.from_uci("e2e4"), 1, True),  # White's first move
        (chess.Move.from_uci("e7e5"), 2, False),  # Black's response
        (chess.Move.from_uci("g1f3"), 3, True),  # White's second move
        (chess.Move.from_uci("b8c6"), 4, False),  # Black's second move
        (chess.Move.from_uci("f1c4"), 5, True),  # White's third move
    ]

    # Add moves with slight delay to see them appear
    def add_move(index):
        if index < len(test_moves):
            move, move_num, is_white = test_moves[index]
            gui.add_move_to_history(move, move_num, is_white)
            print(f"Added move {move_num}: {move} ({'White' if is_white else 'Black'})")
            # Schedule next move
            gui.root.after(1000, lambda: add_move(index + 1))

    # Start adding moves after 2 seconds
    gui.root.after(2000, lambda: add_move(0))

    # Test suggestion
    gui.root.after(
        3000,
        lambda: gui.update_suggestion(
            chess.Move.from_uci("d2d3"),
            {
                "depth": 15,
                "score": chess.engine.PovScore(chess.engine.Cp(50), chess.WHITE),
            },
        ),
    )

    gui.run()


if __name__ == "__main__":
    test_move_history()
