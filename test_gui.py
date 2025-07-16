"""Test script to verify GUI loads correctly"""

import sys

sys.path.append(".")

import chess

from src.gui.main_window import ChessBotGUI

# Create a simple test
gui = ChessBotGUI()

# Test with some dummy data
gui.update_board(chess.Board())
gui.update_game_info(
    {"our_color": "white", "turn": True, "move_number": 1, "game_active": True}
)

# Show a test suggestion
test_move = chess.Move.from_uci("e2e4")
gui.update_suggestion(test_move, {"depth": 5})

gui.add_log("Test GUI loaded successfully!", "success")
gui.add_log("Testing different log levels:", "info")
gui.add_log("This is a warning", "warning")
gui.add_log("This is an error", "error")

print("GUI test loaded. Close the window to exit.")
gui.run()
