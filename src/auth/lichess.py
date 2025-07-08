"""Lichess Authentication"""

from loguru import logger
from selenium.webdriver.common.by import By

from ..config import ConfigManager
from ..core.browser import BrowserManager


class LichessAuth:
    """Handles Lichess authentication"""

    def __init__(self, config_manager: ConfigManager, browser_manager: BrowserManager):
        self.config_manager = config_manager
        self.browser_manager = browser_manager

    def sign_in(self) -> bool:
        """Sign in to Lichess"""
        logger.info("Starting sign-in process")

        try:
            driver = self.browser_manager.get_driver()

            # Click sign-in button
            signin_button = driver.find_element(
                by=By.XPATH, value="/html/body/header/div[2]/a"
            )
            signin_button.click()
            logger.info("Clicked sign-in button")

            # Enter credentials
            lichess_config = self.config_manager.lichess_config
            username_field = driver.find_element(By.ID, "form3-username")
            password_field = driver.find_element(By.ID, "form3-password")
            logger.info("Found username and password fields")

            # Use standardized lowercase keys with backward compatibility
            username_value = lichess_config.get(
                "username", lichess_config.get("Username", "")
            )
            password_value = lichess_config.get(
                "password", lichess_config.get("Password", "")
            )

            username_field.send_keys(username_value)
            password_field.send_keys(password_value)
            logger.info(f"Entered credentials for user: {username_value}")

            # Submit form
            driver.find_element(
                By.XPATH, "/html/body/div/main/form/div[1]/button"
            ).click()
            logger.info("Submitted login form")

            return True

        except Exception as e:
            logger.error(f"Failed during sign-in process: {e}")
            return False
