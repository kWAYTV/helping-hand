"""Chess Bot - Main Entry Point"""

import signal
import sys

from loguru import logger

from src.config import ConfigManager
from src.core.game import GameManager
from src.utils.helpers import clear_screen, signal_handler


def main():
    """Main entry point for the chess bot"""
    try:
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)

        # Clear screen and start
        clear_screen()

        # Get log level from config first
        config_manager = ConfigManager()
        log_level = config_manager.log_level

        # Set log level (keeps default loguru format)
        logger.remove()
        logger.add(sys.stderr, level=log_level)

        # Initialize and start the game manager
        game_manager = GameManager()
        game_manager.start()

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
    finally:
        # Cleanup if game_manager exists
        try:
            if "game_manager" in locals():
                game_manager.cleanup()
        except:
            pass


if __name__ == "__main__":
    main()
