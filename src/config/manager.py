"""Configuration Manager - Centralized config handling with singleton pattern"""

import configparser
import os
from typing import Any, Dict


class ConfigManager:
    """Singleton configuration manager for the chess bot"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.config = configparser.ConfigParser()
            self.config_file = "config.ini"

            # Default configuration with hyphenated keys
            self.defaults = {
                "engine": {
                    "path": "deps/stockfish/stockfish.exe",
                    "depth": "5",
                    "hash": "2048",
                    "skill-level": "14",
                },
                "lichess": {
                    "username": "",
                    "password": "",
                    "totp-secret": "",
                },
                "general": {
                    "move-key": "end",
                    "arrow": "true",
                    "auto-play": "true",
                },
                "humanization": {
                    "min-delay": "0.3",
                    "max-delay": "1.8",
                    "moving-min-delay": "0.5",
                    "moving-max-delay": "2.5",
                    "thinking-min-delay": "0.8",
                    "thinking-max-delay": "3.0",
                },
            }

            self._load_config()
            ConfigManager._initialized = True

    def _load_config(self) -> None:
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            # Create default config if it doesn't exist
            self._create_default_config()

    def _create_default_config(self) -> None:
        """Create a default configuration file"""
        for section, options in self.defaults.items():
            self.config.add_section(section)
            for key, value in options.items():
                self.config.set(section, key, value)

        with open(self.config_file, "w") as f:
            self.config.write(f)

    def get(self, section: str, key: str, fallback: Any = None) -> str:
        """Get a configuration value"""
        if self.config.has_option(section, key):
            return self.config.get(section, key, fallback=fallback)

        # Use defaults if available
        if section in self.defaults and key in self.defaults[section]:
            return self.defaults[section][key]

        return fallback

    @property
    def is_autoplay_enabled(self) -> bool:
        """Check if autoplay is enabled"""
        return self.get("general", "auto-play", "false").lower() == "true"

    @property
    def move_key(self) -> str:
        """Get the move key"""
        return self.get("general", "move-key", "end")

    @property
    def show_arrow(self) -> bool:
        """Check if arrow display is enabled"""
        return self.get("general", "arrow", "true").lower() == "true"

    def get_skill_level(self) -> int:
        """Get engine skill level"""
        return int(self.get("engine", "skill-level", "14"))

    def get_totp_secret(self) -> str:
        """Get TOTP secret"""
        return self.get("lichess", "totp-secret", "").strip()

    def get_general_delays(self) -> tuple[float, float]:
        """Get general action delays"""
        min_delay = self._get_delay_value("min-delay", 0.3)
        max_delay = self._get_delay_value("max-delay", 1.8)
        return min_delay, max_delay

    def get_moving_delays(self) -> tuple[float, float]:
        """Get move execution delays"""
        min_delay = self._get_delay_value("moving-min-delay", 0.5)
        max_delay = self._get_delay_value("moving-max-delay", 2.5)
        return min_delay, max_delay

    def get_thinking_delays(self) -> tuple[float, float]:
        """Get engine thinking delays"""
        min_delay = self._get_delay_value("thinking-min-delay", 0.8)
        max_delay = self._get_delay_value("thinking-max-delay", 3.0)
        return min_delay, max_delay

    def _get_delay_value(self, key: str, default: float) -> float:
        """Get delay value with validation"""
        value = self.get("humanization", key, str(default))

        try:
            delay = float(value)
            # Validate range
            return max(0.1, min(10.0, delay))
        except (ValueError, TypeError):
            return default

    def get_section(self, section: str) -> Dict[str, str]:
        """Get entire configuration section"""
        if self.config.has_section(section):
            return dict(self.config[section])
        return {}

    def set(self, section: str, key: str, value: str) -> None:
        """Set configuration value"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, value)

    def save(self) -> None:
        """Save configuration to file"""
        with open(self.config_file, "w") as f:
            self.config.write(f)

    @property
    def engine_config(self) -> Dict[str, str]:
        """Get engine configuration"""
        return self.get_section("engine")

    @property
    def lichess_config(self) -> Dict[str, str]:
        """Get Lichess configuration"""
        return self.get_section("lichess")

    @property
    def general_config(self) -> Dict[str, str]:
        """Get general configuration"""
        return self.get_section("general")
