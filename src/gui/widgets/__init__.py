"""GUI Widgets package"""

from .chess_board import ChessBoardWidget
from .game_info import GameInfoWidget
from .log_panel import LogPanelWidget
from .move_history import MoveHistoryWidget
from .result_popup import show_game_result

__all__ = [
    "ChessBoardWidget",
    "GameInfoWidget",
    "LogPanelWidget",
    "MoveHistoryWidget",
    "show_game_result",
]
