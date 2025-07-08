"""Chess Engine - Stockfish integration"""

from typing import Any, Dict, Optional

import chess
import chess.engine
from loguru import logger

from ..config import ConfigManager


class ChessEngine:
    """Chess engine wrapper for Stockfish"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.engine: Optional[chess.engine.SimpleEngine] = None
        self._initialize_engine()

    def _initialize_engine(self) -> None:
        """Initialize the chess engine"""
        try:
            engine_config = self.config_manager.engine_config
            # Use standardized lowercase keys with backward compatibility
            engine_path = engine_config.get("path", engine_config.get("Path", ""))

            if not engine_path:
                raise ValueError("Engine path not found in config")

            self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
            logger.info(f"Started chess engine: {engine_path}")

            # Configure engine options using standardized lowercase keys
            skill_level = int(
                engine_config.get(
                    "skilllevel",
                    engine_config.get(
                        "skill level", engine_config.get("Skill Level", 14)
                    ),
                )
            )
            hash_size = int(engine_config.get("hash", engine_config.get("Hash", 2048)))

            options = {
                "Skill Level": skill_level,
                "Hash": hash_size,
            }

            self.engine.configure(options)
            logger.info(
                f"Engine configured - Skill: {options['Skill Level']}, Hash: {options['Hash']}"
            )

        except Exception as e:
            logger.error(f"Failed to start chess engine: {e}")
            raise

    def get_best_move(
        self, board: chess.Board, depth: Optional[int] = None
    ) -> chess.engine.PlayResult:
        """Get the best move for the current position"""
        if not self.engine:
            raise RuntimeError("Engine not initialized")

        if depth is None:
            # Use standardized lowercase key with backward compatibility
            depth = int(
                self.config_manager.get(
                    "engine", "depth", self.config_manager.get("engine", "Depth", 5)
                )
            )

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
