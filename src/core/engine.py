"""Chess Engine - Stockfish engine management"""

import subprocess
from typing import Any, Dict, Optional

import chess
import chess.engine
from loguru import logger

from ..config import ConfigManager


class ChessEngine:
    """Manages Stockfish chess engine interactions"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.engine: Optional[chess.engine.SimpleEngine] = None
        self._initialize_engine()

    def _initialize_engine(self) -> None:
        """Initialize the Stockfish engine"""
        engine_config = self.config_manager.engine_config
        engine_path = engine_config.get("path", "stockfish")

        try:
            # Test if engine exists and is working
            result = subprocess.run(
                [engine_path], capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                raise FileNotFoundError(f"Engine at {engine_path} failed to start")

            # Initialize engine
            self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
            logger.info(f"Chess engine initialized: {engine_path}")

            # Configure engine
            self.engine.configure(
                {
                    "Hash": int(engine_config.get("hash", "2048")),
                    "Skill Level": self.config_manager.get_skill_level(),
                }
            )
            logger.info("Engine configured successfully")

        except Exception as e:
            logger.error(f"Failed to initialize chess engine: {e}")
            raise

    def get_best_move(
        self, board: chess.Board, depth: Optional[int] = None
    ) -> chess.engine.PlayResult:
        """Get the best move for the current position"""
        if not self.engine:
            raise RuntimeError("Engine not initialized")

        if depth is None:
            depth = int(self.config_manager.get("engine", "depth", "5"))

        logger.debug(f"Calculating best move (depth: {depth})")

        result = self.engine.play(
            board,
            chess.engine.Limit(depth=depth),
            game=object,
            info=chess.engine.INFO_NONE,
        )

        logger.debug(f"Engine suggests: {result.move}")
        return result

    def analyze_position(
        self, board: chess.Board, time_limit: float = 1.0
    ) -> Dict[str, Any]:
        """Analyze the current position"""
        if not self.engine:
            raise RuntimeError("Engine not initialized")

        info = self.engine.analyse(board, chess.engine.Limit(time=time_limit))

        return info

    def is_running(self) -> bool:
        """Check if engine is running"""
        return self.engine is not None

    def quit(self) -> None:
        """Stop the chess engine"""
        if self.engine:
            logger.info("Stopping chess engine")
            self.engine.quit()
            self.engine = None
