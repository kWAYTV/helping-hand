"""Lichess Authentication"""

import time

import pyotp
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

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

            # Wait for login form
            time.sleep(2)

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

            # Wait for potential 2FA prompt
            time.sleep(3)

            # Check for 2FA authentication code prompt
            self._handle_2fa_if_required()

            return True

        except Exception as e:
            logger.error(f"Failed during sign-in process: {e}")
            return False

    def _handle_2fa_if_required(self) -> None:
        """Handle 2FA authentication if required"""
        try:
            # Check if 2FA prompt exists (case insensitive)
            auth_label = self.browser_manager.check_exists_by_xpath(
                "/html/body/div[1]/main/form/div[2]/div/label"
            )

            if auth_label and "authentication code" in auth_label.text.lower():
                logger.info("2FA authentication required")

                # Get TOTP secret from config
                lichess_config = self.config_manager.lichess_config
                totp_secret = lichess_config.get("totpsecret", "").strip()

                if totp_secret:
                    # Automatic 2FA using TOTP
                    self._handle_automatic_2fa(totp_secret)
                else:
                    # Manual 2FA input
                    self._handle_manual_2fa()
            else:
                logger.debug("No 2FA prompt detected, continuing...")

        except Exception as e:
            logger.warning(f"Error checking for 2FA prompt: {e}")

    def _handle_automatic_2fa(self, totp_secret: str) -> None:
        """Handle automatic 2FA using TOTP secret"""
        try:
            logger.info("Generating TOTP code automatically")

            # Generate TOTP code
            totp = pyotp.TOTP(totp_secret)
            auth_code = totp.now()

            logger.info(f"Generated 2FA code: {auth_code}")

            # Find and fill the 2FA input field
            driver = self.browser_manager.get_driver()
            auth_input = driver.find_element(
                By.XPATH, "/html/body/div[1]/main/form/div[2]/div/input"
            )
            auth_input.clear()
            auth_input.send_keys(auth_code)

            # Submit the form
            auth_input.send_keys(Keys.RETURN)

            # Wait for authentication to complete
            time.sleep(3)
            logger.info("Automatic 2FA authentication completed")

        except Exception as e:
            logger.error(f"Failed automatic 2FA: {e}")
            # Fallback to manual input
            logger.info("Falling back to manual 2FA input")
            self._handle_manual_2fa()

    def _handle_manual_2fa(self) -> None:
        """Handle manual 2FA input - wait for user"""
        try:
            logger.warning(
                "⚠️  2FA REQUIRED: Please manually enter your authentication code on the webpage"
            )
            logger.warning(
                "💡 TIP: Add your TOTP secret to config [lichess] totpsecret= for automatic 2FA"
            )

            # Wait for user to complete 2FA manually
            # Check periodically if we've moved past the 2FA page
            max_wait_time = 300  # 5 minutes max wait
            check_interval = 2  # Check every 2 seconds
            elapsed_time = 0

            while elapsed_time < max_wait_time:
                time.sleep(check_interval)
                elapsed_time += check_interval

                # Check if we're still on 2FA page
                auth_label = self.browser_manager.check_exists_by_xpath(
                    "/html/body/div[1]/main/form/div[2]/div/label"
                )

                if (
                    not auth_label
                    or "authentication code" not in auth_label.text.lower()
                ):
                    logger.info("2FA completed successfully by user")
                    return

                # Log progress every 30 seconds
                if elapsed_time % 30 == 0:
                    logger.info(
                        f"Still waiting for manual 2FA input... ({elapsed_time}s elapsed)"
                    )

            logger.warning("2FA wait timeout reached - continuing anyway")

        except Exception as e:
            logger.error(f"Error during manual 2FA wait: {e}")
