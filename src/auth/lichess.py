"""Lichess Authentication"""

import time

import pyotp
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
        try:
            # First try loading saved cookies
            if self._try_cookie_login():
                return True

            # Fall back to username/password login
            if self._username_password_login():
                return True

            return False

        except Exception as e:
            logger.error(f"Failed during sign-in process: {e}")
            return False

    def _try_cookie_login(self) -> bool:
        """Try to login using saved cookies"""
        logger.debug("Attempting cookie-based login")

        # Load cookies and check if we're logged in
        cookies_loaded = self.browser_manager.load_cookies()
        if not cookies_loaded:
            return False

        # Refresh the page to apply cookies
        driver = self.browser_manager.get_driver()
        driver.refresh()
        time.sleep(2)

        if self.browser_manager.is_logged_in():
            logger.success("Successfully logged in using saved cookies")
            return True
        else:
            logger.debug("Saved cookies are invalid or expired, clearing them")
            self.browser_manager.clear_cookies()
            return False

    def _username_password_login(self) -> bool:
        """Login using username and password"""
        logger.debug("Attempting username/password login")

        try:
            driver = self.browser_manager.get_driver()

            # Click sign-in button
            signin_button = driver.find_element(
                by=By.XPATH, value="/html/body/header/div[2]/a"
            )
            signin_button.click()
            logger.debug("Clicked sign-in button")

            # Enter credentials
            lichess_config = self.config_manager.lichess_config
            username_field = driver.find_element(By.ID, "form3-username")
            password_field = driver.find_element(By.ID, "form3-password")
            logger.debug("Found username and password fields")

            # Use standardized lowercase keys with backward compatibility
            username_value = lichess_config.get(
                "username", lichess_config.get("Username", "")
            )
            password_value = lichess_config.get(
                "password", lichess_config.get("Password", "")
            )

            username_field.send_keys(username_value)
            password_field.send_keys(password_value)
            logger.debug(f"Entered credentials for user: {username_value}")

            # Submit form
            driver.find_element(
                By.XPATH, "/html/body/div/main/form/div[1]/button"
            ).click()
            logger.debug("Submitted login form")

            # Handle TOTP if needed
            if not self._handle_totp():
                return False

            logger.success("Login successful")
            return True

        except Exception as e:
            logger.error(f"Failed during username/password login: {e}")
            return False

    def _handle_totp(self) -> bool:
        """Handle TOTP authentication if required"""
        try:
            driver = self.browser_manager.get_driver()

            # Wait a bit to see if TOTP is required
            time.sleep(2)

            # Check if we need TOTP (look for "authentication code" text)
            page_text = driver.page_source.lower()
            if "authentication code" not in page_text:
                logger.debug("No TOTP required")
                return True

            logger.info("TOTP authentication required")

            # Try to find TOTP input field
            totp_field = None
            possible_selectors = [
                "input[name='token']",
                "input[placeholder*='code']",
                "input[type='text'][maxlength='6']",
                "#form3-token",
                ".form-group input[type='text']",
            ]

            for selector in possible_selectors:
                try:
                    totp_field = driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue

            if not totp_field:
                logger.error("Could not find TOTP input field")
                return False

            # Get TOTP code
            totp_code = self._get_totp_code()
            if not totp_code:
                logger.error("Could not generate TOTP code")
                return False

            # Enter TOTP code
            totp_field.clear()
            totp_field.send_keys(totp_code)
            logger.debug("Entered TOTP code")

            # Submit TOTP form
            try:
                submit_button = driver.find_element(
                    By.CSS_SELECTOR, "button[type='submit']"
                )
                submit_button.click()
                logger.debug("Submitted TOTP form")
            except:
                # Try alternative submit methods
                totp_field.submit()
                logger.debug("Submitted TOTP form via input")

            return True

        except Exception as e:
            logger.error(f"Failed to handle TOTP: {e}")
            return False

    def _get_totp_code(self) -> str:
        """Generate TOTP code from secret"""
        totp_secret = self.config_manager.totp_secret

        if not totp_secret:
            logger.error("No TOTP secret configured")
            return ""

        try:
            totp = pyotp.TOTP(totp_secret)
            code = totp.now()
            logger.debug(f"Generated TOTP code: {code}")
            return code
        except Exception as e:
            logger.error(f"Failed to generate TOTP code: {e}")
            return ""
