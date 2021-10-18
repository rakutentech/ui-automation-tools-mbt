import re
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from uiautomationtools.logging.logger import Logger
import uiautomationtools.helpers.directory_helpers as dh
from uiautomationtools.proxy.proxy import Proxy


class SeleniumRemote(webdriver.Remote):
    """
    This is an extension of the webdriver.Remote class.
    """

    def __init__(self, command_executor=None, browser='chrome', desired_capabilities=None, proxy=False,
                 keep_alive=False, file_detector=None, options=None, headless=False):
        """
        This constructor for SeleniumRemote. If no executor is provided the webdriver will open locally.

        Args:
            command_executor (None|str): Either a string representing URL of the remote server or a custom
                                         remote_connection.RemoteConnection object. http://127.0.0.1:4444/wd/hub'
            browser (str): The browser name (chrome, firefox, safari).
            desired_capabilities (None|dict): A dictionary of capabilities to request when starting the browser session.
            proxy (bool|str): A proxy address "IP:Port or True (default address)".
            keep_alive (None|bool): Whether to configure remote_connection.RemoteConnection to use HTTP keep-alive.
            file_detector (None): Pass custom file detector object during instantiation. If None, then default
                                  LocalFileDetector() will be used.
            options (None|options.Options): Instance of a driver options.Options class.
            headless (bool): Whether to run in headless mode.
        """
        self.logging = Logger()
        self.logger = self.logging.logger

        capabilities = DesiredCapabilities.__dict__[browser.upper()]
        if desired_capabilities:
            capabilities.update(desired_capabilities)

        self.custom_proxy = None
        if proxy:
            dump_path = f'{self.logging.log_dir}/proxy/dumpfile'
            self.custom_proxy = Proxy(dump_path)
            self.custom_proxy.start_proxy_dump()
        if proxy is True:
            proxy = "localhost:8080"

        if not command_executor:
            options = None
            executable_path = None
            browser_lower = browser.lower()
            driver_path = f'{dh.get_root_dir()}/drivers'
            platform = re.sub(r'\d+', '', sys.platform)
            if 'chrome' in browser_lower:
                options = webdriver.ChromeOptions()
                executable_path = f'{driver_path}/{platform}_chromedriver'

                if proxy:
                    options.add_argument(f'--proxy-server={proxy}')

            elif 'firefox' in browser_lower:
                options = webdriver.FirefoxOptions()
                executable_path = f'{driver_path}/{platform}_geckodriver'
            elif 'safari' in browser_lower:
                executable_path = '/usr/bin/safaridriver'

            if options and headless:
                options.add_argument('--headless')

            if options and platform == 'linux':
                options.add_argument('--disable-gpu')
                options.add_argument('--no-sandbox')

            self.service = Service(executable_path)
            self.service.start()
            # self.service.stop()
            command_executor = self.service.service_url

        super().__init__(command_executor, capabilities, None, None, keep_alive, file_detector, options)
