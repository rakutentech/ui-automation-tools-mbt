import re
import os
import sys

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from uiautomationtools.logging.logger import Logger
import uiautomationtools.helpers.directory_helpers as dh
from uiautomationtools.proxy.proxy import Proxy
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager


class SeleniumRemote(webdriver.Remote):
    """
    This is an extension of the webdriver.Remote class.
    """

    def __init__(self, command_executor=None, browser='chrome', desired_capabilities=None,
                 proxy=False, keep_alive=False, file_detector=None,
                 options=None, headless=False):
        """
        This constructor for SeleniumRemote. If no executor is provided the webdriver will open locally.

        Args:
            command_executor: Either a string representing URL of the remote server or a custom
                                         remote_connection.RemoteConnection object. http://127.0.0.1:4444/wd/hub'
            browser: The browser name (chrome, firefox, safari).
            desired_capabilities: A dictionary of capabilities to request when starting the browser session.
            proxy: A proxy address "IP:Port or True (default address)".
            keep_alive: Whether to configure remote_connection.RemoteConnection to use HTTP keep-alive.
            file_detector (None): Pass custom file detector object during instantiation. If None, then default
                                  LocalFileDetector() will be used.
            options (None|options.Options): Instance of a driver options.Options class.
            headless: Whether to run in headless mode.
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

        browser_lower = browser.lower()
        if not options:
            if "chrome" in browser_lower:
                options = webdriver.ChromeOptions()

                if proxy:
                    options.add_argument(f'--proxy-server={proxy}')
            elif "firefox" in browser_lower:
                options = webdriver.FirefoxOptions()

        if headless:
            options.add_argument('--headless')

        platform = re.sub(r'\d+', '', sys.platform)
        if platform == 'linux':
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')

        if not command_executor:
            if 'safari' in browser_lower:
                executable_path = '/usr/bin/safaridriver'
            else:
                root_directory = dh.get_root_dir()
                driver_directory = f'{os.path.join(root_directory, ".wdm")}/drivers.json'
                drivers = dh.load_json(driver_directory)

                for key, value in drivers.copy().items():
                    version = next(p for p in value['binary_path'].split('/') if '.' in p and re.findall(r'\d+', p))
                    drivers[version] = drivers.pop(key)

                sorted_versions = sorted(drivers.keys(), key=lambda s: list(map(int, s.split('.'))), reverse=True)
                latest_version = sorted_versions[0]

                executable_path = ""
                if drivers:
                    executable_path = f'{root_directory}{drivers[latest_version]["binary_path"]}'

            try:
                self.service = Service(executable_path)
                self.service.start()
                # self.service.stop()
                command_executor = self.service.service_url
                super().__init__(command_executor, capabilities, None, None, keep_alive, file_detector, options)
            except Exception:
                os.environ['WDM_LOCAL'] = '0'

                if "chrome" in browser_lower:
                    executable_path = ChromeDriverManager(path=root_directory).install()
                elif "firefox" in browser_lower:
                    executable_path = GeckoDriverManager(path=root_directory).install()

                drivers_json = dh.load_json(driver_directory)
                for d in drivers_json.values():
                    d['binary_path'] = d['binary_path'].replace(root_directory, '')
                dh.make_json(drivers_json, driver_directory, append=True)

                self.service = Service(executable_path)
                self.service.start()
                command_executor = self.service.service_url
                super().__init__(command_executor, capabilities, None, None, keep_alive, file_detector, options)
