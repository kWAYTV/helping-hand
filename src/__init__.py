"""
Chess Bot - Professional modular implementation
"""

__author__ = "Chess Bot"

# Import main components
from .config.manager import ConfigManager
from .core.game import GameManager

__all__ = ["GameManager", "ConfigManager"]
