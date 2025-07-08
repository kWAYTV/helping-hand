"""Browser Manager - Singleton pattern for WebDriver management"""

import json
import os
from typing import Optional

from loguru import logger
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from ..utils.helpers import get_geckodriver_path


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
            webdriver_options = webdriver.FirefoxOptions()
            webdriver_options.add_argument(
                f'--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0"'
            )

            firefox_service = webdriver.firefox.service.Service(
                executable_path=get_geckodriver_path()
            )

            self.driver = webdriver.Firefox(
                service=firefox_service, options=webdriver_options
            )
            logger.debug("Firefox WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise

    def get_driver(self) -> webdriver.Firefox:
        """Get the WebDriver instance"""
        if self.driver is None:
            raise RuntimeError("WebDriver not initialized")
        return self.driver

    def navigate_to(self, url: str) -> None:
        """Navigate to a URL"""
        if self.driver:
            logger.debug(f"Navigating to: {url}")
            self.driver.get(url)
        else:
            raise RuntimeError("WebDriver not initialized")

    def check_exists_by_xpath(self, xpath: str):
        """Check if element exists by XPath"""
        try:
            element = self.driver.find_element(By.XPATH, xpath)
            return element
        except NoSuchElementException:
            return False

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

    def hide_username_elements(self) -> None:
        """Hide username elements to prevent data leakage"""
        if not self.driver:
            return

        # Hide username after login
        self._hide_element_by_xpath('//*[@id="user_tag"]')

        # Hide username in game page
        self._hide_element_by_xpath("/html/body/div[2]/main/div[1]/div[6]/a")

        logger.debug("Username elements hidden for privacy")

    def _hide_element_by_xpath(self, xpath: str) -> None:
        """Hide element by XPath using JavaScript"""
        script = f"""
        try {{
            var element = document.evaluate('{xpath}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            if (element) {{
                element.style.visibility = 'hidden';
                element.style.opacity = '0';
                console.log('Hidden element at xpath: {xpath}');
            }}
        }} catch (e) {{
            console.log('Could not hide element at xpath: {xpath}', e);
        }}
        """
        self.execute_script(script)

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
                logger.debug(f"Saved {len(cookies)} cookies to {self.cookies_file}")
            except Exception as e:
                logger.error(f"Failed to save cookies: {e}")

    def load_cookies(self) -> bool:
        """Load cookies from file and apply them"""
        if not os.path.exists(self.cookies_file):
            logger.info("No saved cookies found")
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

                logger.debug(f"Loaded {len(cookies)} cookies")
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
                logger.debug("Cleared browser cookies")

            # Clear saved cookies file
            if os.path.exists(self.cookies_file):
                os.remove(self.cookies_file)
                logger.debug("Cleared saved cookies file")
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
            # Look for user menu or account indicator
            user_indicators = [
                "#user_tag",  # User menu
                ".site-title .user",  # Username in header
                "[data-icon='H']",  # User icon
                ".dasher .toggle",  # Dasher menu
            ]

            for selector in user_indicators:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element and element.text.strip():
                        logger.debug(f"Login detected via selector: {selector}")
                        return True
                except:
                    continue

            # Check page source for login indicators
            page_source = self.driver.page_source.lower()
            if any(
                indicator in page_source
                for indicator in ["logout", "preferences", "profile"]
            ):
                logger.debug("Login detected via page source")
                return True

            return False

        except Exception as e:
            logger.debug(f"Error checking login status: {e}")
            return False

    def close(self) -> None:
        """Close the browser"""
        if self.driver:
            logger.info("Closing browser, press Ctrl+C to force quit")
            self.driver.quit()
            self.driver = None
