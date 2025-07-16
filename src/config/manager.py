"""Configuration Manager - Singleton pattern for config handling"""

import configparser
import os
from typing import Any, Dict, Optional

from loguru import logger

from ..utils.helpers import get_stockfish_path


class ConfigManager:
    """Singleton configuration manager for the chess bot"""

    _instance: Optional["ConfigManager"] = None
    _initialized: bool = False

    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.config = configparser.ConfigParser()
            self._config_path = "config.ini"
            self._load_or_create_config()
            ConfigManager._initialized = True

    def _load_or_create_config(self) -> None:
        """Load existing config or create default one"""
        if os.path.isfile(self._config_path):
            self.config.read(self._config_path)
            logger.debug("Loaded existing config.ini")
        else:
            logger.debug("No config.ini found, creating default config")
            self._create_default_config()
            self.config.read(self._config_path)

    def _create_default_config(self) -> None:
        """Create default configuration file"""
        self.config["engine"] = {
            "path": get_stockfish_path(),
            "depth": "5",
            "hash": "2048",
            "skill-level": "14",
        }
        self.config["lichess"] = {
            "username": "user",
            "password": "pass",
            "totp-secret": "",
        }
        self.config["general"] = {
            "move-key": "end",
            "arrow": "true",
            "auto-play": "true",
            "log-level": "INFO",
        }
        self.config["humanization"] = {
            "min-delay": "0.3",
            "max-delay": "1.8",
            "moving-min-delay": "0.5",
            "moving-max-delay": "2.5",
            "thinking-min-delay": "0.8",
            "thinking-max-delay": "3.0",
        }

        with open(self._config_path, "w") as configfile:
            self.config.write(configfile)

    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """Get configuration value with fallback"""
        try:
            return self.config[section].get(key, fallback)
        except KeyError:
            logger.warning(f"Section '{section}' not found in config")
            return fallback

    def get_section(self, section: str) -> Dict[str, str]:
        """Get entire configuration section"""
        try:
            return dict(self.config[section])
        except KeyError:
            logger.warning(f"Section '{section}' not found in config")
            return {}

    def set(self, section: str, key: str, value: str) -> None:
        """Set configuration value"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value

    def save(self) -> None:
        """Save configuration to file"""
        with open(self._config_path, "w") as configfile:
            self.config.write(configfile)

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

    @property
    def is_autoplay_enabled(self) -> bool:
        """Check if autoplay is enabled"""
        # Check both new hyphenated and old mixed case for backward compatibility
        value = self.get(
            "general", "auto-play", self.get("general", "AutoPlay", "false")
        )
        return value.lower() == "true"

    @property
    def move_key(self) -> str:
        """Get the move key"""
        # Check both new hyphenated and old mixed case for backward compatibility
        return self.get("general", "move-key", self.get("general", "MoveKey", "end"))

    @property
    def show_arrow(self) -> bool:
        """Check if arrow should be shown"""
        # Check both new hyphenated and old mixed case for backward compatibility
        value = self.get("general", "arrow", self.get("general", "Arrow", "true"))
        return value.lower() == "true"

    @property
    def totp_secret(self) -> str:
        """Get the TOTP secret"""
        return self.get("lichess", "totp-secret", "")

    @property
    def humanization_config(self) -> Dict[str, str]:
        """Get humanization configuration"""
        return self.get_section("humanization")

    @property
    def log_level(self) -> str:
        """Get the log level"""
        level = self.get("general", "log-level", "INFO").upper()
        # Validate log level
        valid_levels = [
            "TRACE",
            "DEBUG",
            "INFO",
            "SUCCESS",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ]
        if level not in valid_levels:
            logger.warning(f"Invalid log level '{level}', using INFO")
            return "INFO"
        return level

    def get_humanization_delay(self, delay_type: str) -> tuple[float, float]:
        """Get min/max delays for humanization"""
        config = self.humanization_config
        if delay_type == "base":
            min_delay = float(config.get("min-delay", "0.3"))
            max_delay = float(config.get("max-delay", "1.8"))
        elif delay_type == "moving":
            min_delay = float(config.get("moving-min-delay", "0.5"))
            max_delay = float(config.get("moving-max-delay", "2.5"))
        elif delay_type == "thinking":
            min_delay = float(config.get("thinking-min-delay", "0.8"))
            max_delay = float(config.get("thinking-max-delay", "3.0"))
        else:
            # Default to base delays
            min_delay = float(config.get("min-delay", "0.3"))
            max_delay = float(config.get("max-delay", "1.8"))

        return min_delay, max_delay
