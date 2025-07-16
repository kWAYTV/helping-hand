"""Custom loguru handler for GUI integration"""

import sys
from typing import Optional

from loguru import logger


class GUILogHandler:
    """Custom log handler that sends messages to GUI"""

    def __init__(self, gui_instance=None):
        self.gui_instance = gui_instance
        self.handler_id = None

    def set_gui_instance(self, gui_instance):
        """Set the GUI instance to send logs to"""
        self.gui_instance = gui_instance

    def write(self, message):
        """Write method for loguru compatibility"""
        if self.gui_instance:
            # Parse log level from message
            level = self._extract_level_from_message(message)
            clean_message = self._clean_message(message)

            # Send to GUI
            self.gui_instance.log_message(level, clean_message)

    def _extract_level_from_message(self, message: str) -> str:
        """Extract log level from loguru message"""
        if "| ERROR" in message:
            return "ERROR"
        elif "| WARNING" in message:
            return "WARNING"
        elif "| SUCCESS" in message:
            return "SUCCESS"
        elif "| INFO" in message:
            return "INFO"
        elif "| DEBUG" in message:
            return "DEBUG"
        elif "| TRACE" in message:
            return "TRACE"
        else:
            return "INFO"

    def _clean_message(self, message: str) -> str:
        """Clean the log message for GUI display"""
        # Remove timestamp and log level formatting
        lines = message.strip().split("\n")
        if lines:
            # Find the actual message part (after the | separator)
            main_line = lines[0]
            if " | " in main_line:
                parts = main_line.split(" | ")
                if len(parts) >= 3:
                    # Format: timestamp | level | message
                    return parts[2]
                elif len(parts) == 2:
                    return parts[1]
            return main_line
        return message.strip()

    def flush(self):
        """Flush method for compatibility"""
        pass

    def install_handler(self):
        """Install this handler with loguru"""
        if self.handler_id is None:
            self.handler_id = logger.add(
                self,
                format="{time:HH:mm:ss} | {level} | {message}",
                level="TRACE",
                filter=None,
            )

    def remove_handler(self):
        """Remove this handler from loguru"""
        if self.handler_id is not None:
            logger.remove(self.handler_id)
            self.handler_id = None
