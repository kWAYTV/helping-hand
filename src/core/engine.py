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
            # === ENGINE STARTUP ===
            engine_config = self.config_manager.engine_config
            # Use standardized lowercase keys with backward compatibility
            engine_path = engine_config.get("path", engine_config.get("Path", ""))

            if not engine_path:
                raise ValueError("Engine path not configured")

            self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
            logger.info(f"Stockfish engine initialized: {engine_path}")

            # === ENGINE CONFIGURATION ===
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
                f"Engine configured - Skill Level: {skill_level}, Hash: {hash_size}MB"
            )

        except Exception as e:
            logger.error(f"Failed to initialize Stockfish engine: {e}")
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
            logger.warning("Engine not initialized - attempting restart")
            self._initialize_engine()

        if depth is None:
            # Use standardized hyphenated key with backward compatibility
            depth = int(
                self.config_manager.get(
                    "engine", "depth", self.config_manager.get("engine", "Depth", 5)
                )
            )

        logger.debug(f"Analyzing position (depth: {depth})")

        result = self.engine.play(
            board,
            chess.engine.Limit(depth=depth),
            game=object,
            info=chess.engine.INFO_NONE,
        )

        logger.debug(f"Best move calculated: {result.move}")
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
            logger.warning("Engine not initialized - attempting restart")
            self._initialize_engine()

        logger.debug(f"Running position analysis (time limit: {time_limit}s)")
        info = self.engine.analyse(board, chess.engine.Limit(time=time_limit))

        return info

    def is_running(self) -> bool:
        """Check if engine is running"""
        return self.engine is not None

    def quit(self) -> None:
        """Stop the chess engine"""
        if self.engine:
            logger.debug("Shutting down chess engine")
            safe_execute(self.engine.quit, log_errors=True)
            self.engine = None
