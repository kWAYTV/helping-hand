"""Chess Bot - Main Entry Point"""

import signal
import sys

from loguru import logger

from src.config import ConfigManager
from src.core.game import GameManager
from src.gui.main_window import ChessBotGUI
from src.utils.helpers import clear_screen, signal_handler


class GUILogHandler:
    """Custom log handler that forwards logs to GUI"""

    def __init__(self):
        self.gui = None

    def set_gui(self, gui):
        """Set the GUI instance for log forwarding"""
        self.gui = gui

    def write(self, message):
        """Forward log messages to GUI"""
        try:
            if self.gui and hasattr(message, "record"):
                level = message.record["level"].name.lower()
                text = message.record["message"]

                # Forward to GUI in thread-safe manner
                if hasattr(self.gui, "root") and self.gui.root:
                    self.gui.root.after(0, lambda: self.gui.add_log(text, level))
        except Exception:
            pass  # Silently handle any GUI errors

        # Return empty string to satisfy loguru's expectations
        return ""

    def flush(self):
        """Required method for file-like objects"""
        pass


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

        # Create GUI log handler for dual output
        gui_log_handler = GUILogHandler()

        # Set up logging with both console and GUI output
        logger.remove()
        logger.add(sys.stderr, level=log_level)  # Console logging

        # Add GUI logging with error handling for PyInstaller compatibility
        try:
            logger.add(
                gui_log_handler.write, level=log_level, colorize=False
            )  # GUI logging
        except Exception as e:
            # Fallback to console-only logging if GUI handler fails
            logger.warning(f"Could not set up GUI logging: {e}")
            logger.info("Continuing with console-only logging")

        # Initialize and start the game manager
        game_manager = GameManager()

        # Initialize and setup GUI
        gui = ChessBotGUI(game_manager)
        gui_log_handler.set_gui(gui)

        # Log mode info
        if config_manager.is_autoplay_enabled:
            logger.info("AutoPlay MODE: Bot will make moves automatically")
        else:
            move_key = config_manager.move_key
            logger.info(
                f"Suggestion MODE: Bot will suggest moves (press '{move_key}' to execute)"
            )

        # Start the GUI main loop (this will block)
        gui.run()

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
    finally:
        # Enhanced cleanup with better error handling
        if "game_manager" in locals():
            try:
                game_manager.cleanup()
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup: {cleanup_error}")
                # Force cleanup critical resources
                try:
                    if (
                        hasattr(game_manager, "browser_manager")
                        and game_manager.browser_manager
                    ):
                        if (
                            hasattr(game_manager.browser_manager, "driver")
                            and game_manager.browser_manager.driver
                        ):
                            game_manager.browser_manager.driver.quit()
                except:
                    pass


if __name__ == "__main__":
    main()
