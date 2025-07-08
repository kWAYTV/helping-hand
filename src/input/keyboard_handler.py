"""Keyboard Handler - Input management"""

from typing import Callable, Optional

from loguru import logger
from pynput import keyboard

from ..config import ConfigManager


class KeyboardHandler:
    """Handles keyboard input for manual move execution"""

    def __init__(
        self,
        config_manager: ConfigManager,
        on_move_key_press: Optional[Callable] = None,
    ):
        self.config_manager = config_manager
        self.on_move_key_press = on_move_key_press
        self.listener: Optional[keyboard.Listener] = None
        self.make_move = False

    def on_press(self, key) -> None:
        """Handle key press events"""
        key_string = str(key)
        move_key = self.config_manager.move_key

        if key_string == move_key or key_string == "Key." + move_key:
            self.make_move = True
            logger.debug(f"Move key pressed: {move_key}")
            if self.on_move_key_press:
                self.on_move_key_press()

    def on_release(self, key) -> None:
        """Handle key release events"""
        key_string = str(key)
        move_key = self.config_manager.move_key

        if key_string == move_key or key_string == "Key." + move_key:
            self.make_move = False
            logger.debug(f"Move key released: {move_key}")

    def start_listening(self) -> None:
        """Start the keyboard listener"""
        if self.listener is None:
            self.listener = keyboard.Listener(
                on_press=self.on_press, on_release=self.on_release
            )
            self.listener.start()
            logger.info("Keyboard listener started")

    def stop_listening(self) -> None:
        """Stop the keyboard listener"""
        if self.listener:
            self.listener.stop()
            self.listener = None
            logger.info("Keyboard listener stopped")

    def should_make_move(self) -> bool:
        """Check if move key is currently pressed"""
        return self.make_move

    def reset_move_state(self) -> None:
        """Reset the move state"""
        self.make_move = False
