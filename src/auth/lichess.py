"""Lichess Authentication - Handle login and 2FA"""

import time
from typing import Optional

import pyotp
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from ..config import ConfigManager
from ..core.browser import BrowserManager


class LichessAuth:
    """Handles Lichess authentication including 2FA support"""

    def __init__(self, config_manager: ConfigManager, browser_manager: BrowserManager):
        self.config_manager = config_manager
        self.browser_manager = browser_manager
        self.driver = browser_manager.get_driver()

    def sign_in(self) -> bool:
        """Sign in to Lichess with credentials and handle 2FA if needed"""
        try:
            logger.info("Attempting to sign in to Lichess")

            # Navigate to sign in page
            self.driver.get("https://lichess.org/signin")

            # Get credentials
            lichess_config = self.config_manager.lichess_config
            username = lichess_config.get("username", "")
            password = lichess_config.get("password", "")

            if not username or not password:
                logger.error("Username or password not found in config")
                return False

            # Fill credentials
            username_field = WebDriverWait(self.driver, 10).until(
                ec.presence_of_element_located((By.ID, "form3-username"))
            )
            password_field = self.driver.find_element(By.ID, "form3-password")

            username_field.send_keys(username)
            password_field.send_keys(password)

            # Submit form
            submit_button = self.driver.find_element(
                By.CSS_SELECTOR, ".submit button[type='submit']"
            )
            submit_button.click()

            # Wait a moment for page to process
            time.sleep(2)

            # Check if already logged in (redirected to homepage)
            if "lichess.org" in self.driver.current_url and not any(
                path in self.driver.current_url for path in ["/signin", "/login"]
            ):
                logger.success("Successfully signed in to Lichess")
                return True

            # Check for 2FA prompt (case-insensitive)
            page_text = self.driver.page_source.lower()
            if "authentication code" in page_text or "two-factor" in page_text:
                logger.info("2FA authentication required")
                return self._handle_2fa()

            # Check for errors
            if "error" in page_text or "invalid" in page_text:
                logger.error("Sign in failed - invalid credentials")
                return False

            logger.success("Successfully signed in to Lichess")
            return True

        except Exception as e:
            logger.error(f"Sign in failed: {e}")
            return False

    def _handle_2fa(self) -> bool:
        """Handle 2FA authentication"""
        try:
            # Get TOTP secret
            totp_secret = self.config_manager.get_totp_secret()

            if totp_secret:
                # Generate TOTP code automatically
                logger.info("🔐 Generating 2FA code automatically...")
                totp = pyotp.TOTP(totp_secret)
                auth_code = totp.now()
                logger.info(f"Generated 2FA code: {auth_code}")
            else:
                # Manual 2FA input
                logger.info("⏳ Waiting for manual 2FA input (you have 5 minutes)...")
                logger.info(
                    "💡 TIP: Add your TOTP secret to config [lichess] totp-secret= for automatic 2FA"
                )

                # Wait up to 5 minutes for user to input 2FA manually
                start_time = time.time()
                timeout = 300  # 5 minutes

                while time.time() - start_time < timeout:
                    # Check if we've moved past the 2FA page
                    current_url = self.driver.current_url
                    if "lichess.org" in current_url and not any(
                        path in current_url for path in ["/signin", "/login", "/2fa"]
                    ):
                        logger.success("✅ Manual 2FA completed successfully")
                        return True

                    time.sleep(2)

                logger.error("⏰ Manual 2FA timeout - please try again")
                return False

            # Input the generated code
            try:
                auth_field = WebDriverWait(self.driver, 10).until(
                    ec.presence_of_element_located((By.NAME, "token"))
                )
                auth_field.clear()
                auth_field.send_keys(auth_code)

                # Submit 2FA form
                submit_button = self.driver.find_element(
                    By.CSS_SELECTOR, "button[type='submit']"
                )
                submit_button.click()

                # Wait for redirect
                time.sleep(3)

                # Verify success
                if "lichess.org" in self.driver.current_url and not any(
                    path in self.driver.current_url
                    for path in ["/signin", "/login", "/2fa"]
                ):
                    logger.success("✅ 2FA authentication successful")
                    return True
                else:
                    logger.error("❌ 2FA authentication failed")
                    return False

            except Exception as e:
                logger.error(f"Failed to input 2FA code: {e}")
                return False

        except Exception as e:
            logger.error(f"2FA handling failed: {e}")
            return False
