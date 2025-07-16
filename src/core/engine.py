"""Chess Engine - Stockfish integration"""

from typing import Any, Dict, Optional

import chess
import chess.engine
from loguru import logger

from ..config import ConfigManager
from ..utils.resilience import retry_on_exception, safe_execute


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
            logger.debug(f"Started chess engine: {engine_path}")

            # Configure engine options using standardized hyphenated keys
            skill_level = int(
                engine_config.get(
                    "skill-level",
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
            logger.debug(
                f"Engine configured - Skill: {options['Skill Level']}, Hash: {options['Hash']}"
            )

        except Exception as e:
            logger.error(f"Failed to start chess engine: {e}")
            raise

    @retry_on_exception(
        max_retries=3,
        delay=1.0,
        exceptions=(chess.engine.EngineError, chess.engine.EngineTerminatedError),
    )
    def get_best_move(
        self, board: chess.Board, depth: Optional[int] = None
    ) -> chess.engine.PlayResult:
        """Get the best move for the current position"""
        if not self.engine:
            logger.warning("Engine not initialized, attempting to reinitialize")
            self._initialize_engine()

        if depth is None:
            # Use standardized hyphenated key with backward compatibility
            depth = int(
                self.config_manager.get(
                    "engine", "depth", self.config_manager.get("engine", "Depth", 5)
                )
            )

        logger.debug(f"Calculating best move (depth: {depth})")

        # Get both move and evaluation
        result = self.engine.play(
            board,
            chess.engine.Limit(depth=depth),
            game=object,
            info=chess.engine.INFO_ALL,  # Request all info including evaluation
        )

        # Get detailed analysis for evaluation
        analysis = self.engine.analyse(
            board, chess.engine.Limit(depth=depth), info=chess.engine.INFO_ALL
        )

        # Add evaluation to result
        if hasattr(result, "info"):
            result.info.update(analysis)
        else:
            result.info = analysis

        logger.debug(f"Engine suggests: {result.move}")
        return result

    @retry_on_exception(
        max_retries=2,
        delay=0.5,
        exceptions=(chess.engine.EngineError, chess.engine.EngineTerminatedError),
    )
    def analyze_position(
        self, board: chess.Board, time_limit: float = 1.0
    ) -> Dict[str, Any]:
        """Analyze the current position"""
        if not self.engine:
            logger.warning("Engine not initialized, attempting to reinitialize")
            self._initialize_engine()

        info = self.engine.analyse(board, chess.engine.Limit(time=time_limit))

        return info

    def is_running(self) -> bool:
        """Check if engine is running"""
        return self.engine is not None

    def quit(self) -> None:
        """Stop the chess engine"""
        if self.engine:
            logger.debug("Stopping chess engine")
            safe_execute(self.engine.quit, log_errors=True)
            self.engine = None
