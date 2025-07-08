"""Browser Manager - Singleton pattern for WebDriver management"""

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
            logger.info("Firefox WebDriver initialized successfully")
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
            logger.info(f"Navigating to: {url}")
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

    def close(self) -> None:
        """Close the browser"""
        if self.driver:
            logger.info("Closing browser")
            self.driver.quit()
            self.driver = None
