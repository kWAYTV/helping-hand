"""Browser Manager - Singleton pattern for WebDriver management"""

import json
import os
from typing import Optional

import ua_generator
from loguru import logger
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from ..utils.helpers import get_geckodriver_path, install_firefox_extensions
from ..utils.resilience import browser_retry, element_retry, safe_execute


class BrowserManager:
    """Singleton browser manager for the chess bot"""

    _instance: Optional["BrowserManager"] = None
    _initialized: bool = False

    def __new__(cls) -> "BrowserManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.driver: Optional[webdriver.Firefox] = None
            self.cookies_file = os.path.join("deps", "lichess_cookies.json")
            self._setup_driver()
            BrowserManager._initialized = True

    def _setup_driver(self) -> None:
        """Initialize Firefox WebDriver with options"""
        try:
            # === BROWSER INITIALIZATION ===
            # Generate realistic user agent
            ua = ua_generator.generate(
                browser="firefox", platform=("windows", "macos", "linux")
            )

            webdriver_options = webdriver.FirefoxOptions()
            webdriver_options.add_argument(f'--user-agent="{ua.text}"')

            firefox_service = webdriver.firefox.service.Service(
                executable_path=get_geckodriver_path()
            )

            self.driver = webdriver.Firefox(
                service=firefox_service, options=webdriver_options
            )

            # Install Firefox extensions
            install_firefox_extensions(self.driver)

            logger.info("Firefox WebDriver initialized successfully")
            logger.debug(f"User Agent: {ua.text}")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise

    def get_driver(self) -> webdriver.Firefox:
        """Get the WebDriver instance"""
        if self.driver is None:
            raise RuntimeError("WebDriver not initialized")
        return self.driver

    @browser_retry(max_retries=3, delay=2.0)
    def navigate_to(self, url: str) -> None:
        """Navigate to a URL"""
        if self.driver:
            logger.debug(f"Navigating to: {url}")
            self.driver.get(url)
        else:
            raise RuntimeError("WebDriver not initialized")

    @element_retry(max_retries=2, delay=0.5)
    def check_exists_by_xpath(self, xpath: str):
        """Check if element exists by XPath"""
        try:
            element = self.driver.find_element(By.XPATH, xpath)
            return element
        except NoSuchElementException:
            return False

    @element_retry(max_retries=2, delay=0.5)
    def check_exists_by_class(self, classname: str):
        """Check if element exists by class name"""
        try:
            element = self.driver.find_element(By.CLASS_NAME, classname)
            return element
        except NoSuchElementException:
            return False

    def execute_script(self, script: str, *args):
        """Execute JavaScript in the browser"""
        return self.driver.execute_script(script, *args)

    def save_screenshot(self, filename: str) -> None:
        """Save a screenshot"""
        if self.driver:
            self.driver.save_screenshot(filename)

    @property
    def page_source(self) -> str:
        """Get page source"""
        return self.driver.page_source if self.driver else ""

    @property
    def current_url(self) -> str:
        """Get current URL"""
        return self.driver.current_url if self.driver else ""

    def save_cookies(self) -> None:
        """Save current cookies to file"""
        if self.driver:
            try:
                cookies = self.driver.get_cookies()
                with open(self.cookies_file, "w") as f:
                    json.dump(cookies, f, indent=2)
                logger.debug(f"Saved authentication session ({len(cookies)} cookies)")
            except Exception as e:
                logger.error(f"Failed to save cookies: {e}")

    def load_cookies(self) -> bool:
        """Load cookies from file and apply them"""
        if not os.path.exists(self.cookies_file):
            logger.debug("No saved authentication session found")
            return False

        try:
            with open(self.cookies_file, "r") as f:
                cookies = json.load(f)

            # Must be on the correct domain to add cookies
            if self.driver and self.current_url.startswith("https://lichess.org"):
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        logger.debug(
                            f"Failed to add cookie {cookie.get('name', 'unknown')}: {e}"
                        )

                logger.debug(f"Loaded authentication session ({len(cookies)} cookies)")
                return True
            else:
                logger.debug("Cannot load cookies - not on Lichess domain")
                return False

        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return False

    def clear_cookies(self) -> None:
        """Clear saved cookies file and browser cookies"""
        try:
            # Clear browser cookies
            if self.driver:
                self.driver.delete_all_cookies()
                logger.debug("Cleared browser session")

            # Clear saved cookies file
            if os.path.exists(self.cookies_file):
                os.remove(self.cookies_file)
                logger.debug("Cleared saved session file")
        except Exception as e:
            logger.error(f"Failed to clear cookies: {e}")

    def get_cookies_info(self) -> dict:
        """Get information about saved cookies"""
        if not os.path.exists(self.cookies_file):
            return {"exists": False, "count": 0, "file_size": 0}

        try:
            with open(self.cookies_file, "r") as f:
                cookies = json.load(f)

            file_size = os.path.getsize(self.cookies_file)
            return {
                "exists": True,
                "count": len(cookies),
                "file_size": file_size,
                "file_path": self.cookies_file,
            }
        except Exception as e:
            logger.error(f"Failed to read cookies info: {e}")
            return {"exists": True, "count": 0, "file_size": 0, "error": str(e)}

    def is_logged_in(self) -> bool:
        """Check if we're currently logged in to Lichess"""
        if not self.driver:
            return False

        try:
            page_source = self.driver.page_source

            # FIRST: Check for strong authentication indicators (these override login page detection)
            strong_auth_patterns = [
                'data-user="',  # User data attribute with username
                'data-username="',  # Username data attribute
                'href="/logout"',  # Actual logout link
            ]

            for pattern in strong_auth_patterns:
                if pattern in page_source:
                    # Extract username for confirmation if possible
                    if 'data-user="' in pattern:
                        import re

                        match = re.search(r'data-user="([^"]+)"', page_source)
                        if match:
                            username = match.group(1)
                            logger.debug(
                                f"Authentication confirmed - logged in as: {username}"
                            )
                            return True
                    logger.debug(
                        f"Authentication confirmed via strong indicator: {pattern}"
                    )
                    return True

            # SECOND: Look for logged-in UI elements
            user_indicators = [
                "#user_tag",  # User menu
                "a[href='/logout']",  # Logout link
                ".dasher a",  # User dasher menu
            ]

            for selector in user_indicators:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element and element.is_displayed() and element.text.strip():
                        logger.debug(
                            f"Authentication confirmed via element: {selector} (text: {element.text.strip()})"
                        )
                        return True
                except:
                    continue

            # THIRD: Check for weaker logged-in content patterns
            page_source_lower = page_source.lower()
            logged_in_patterns = [
                'href="/account"',  # Account page link
                'class="user"',  # User class elements
            ]

            for pattern in logged_in_patterns:
                if pattern in page_source_lower:
                    logger.debug(f"Authentication confirmed via pattern: {pattern}")
                    return True

            # FOURTH: Only NOW check for login page indicators (as negative confirmation)
            login_indicators = [
                'class="auth auth-login"',  # Login page class
                "Sign in</h1>",  # Login page heading
                'id="form3-username"',  # Username input field
                'id="form3-password"',  # Password input field
            ]

            for indicator in login_indicators:
                if indicator in page_source:
                    logger.debug(f"Login page detected via: {indicator}")
                    return False

            logger.debug("No clear authentication indicators found")
            return False

        except Exception as e:
            logger.debug(f"Error checking authentication status: {e}")
            return False

    def close(self) -> None:
        """Close the browser"""
        if self.driver:
            logger.info("Closing browser (press Ctrl+C to force quit)")
            self.driver.quit()
            self.driver = None
