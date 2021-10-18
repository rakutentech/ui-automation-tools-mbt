import pyperclip
from glob import iglob

try:
    import pyautogui as pya
except:
    # TODO - need to configure for headless docker images
    print("The package pyautogui isn't supported on headless docker images.")

from selenium.webdriver.common.action_chains import ActionChains

from uiautomationtools.selenium.selenium.selenium_remote import SeleniumRemote
from uiautomationtools.selenium.selenium_appium_shared import SeleniumAppiumShared


class SeleniumExtended(SeleniumRemote, SeleniumAppiumShared):
    """
    This is an extension of SeleniumRemote and SeleniumAppiumShared classes.
    """

    def __init__(self, command_executor=None, browser='chrome', desired_capabilities=None, proxy=False,
                 keep_alive=False, file_detector=None, options=None, language='en', headless=False):
        """
        The constructor for SeleniumExtended.

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
            language (str): The language of the selectors.
            headless (bool): Whether to run in headless mode.
        """
        SeleniumRemote.__init__(self, command_executor, browser, desired_capabilities, proxy,
                                keep_alive, file_detector, options, headless)
        SeleniumAppiumShared.__init__(self)

        self.language = language
        self.action_chains = ActionChains
        self.context = self.name

    def navigate(self, url):
        """
        This navigates to the url.

        Args:
            url (str): The 'http' url to navigate to.
        """
        self.logger.info('\n')
        self.logger.info(f'Navigating to {url}.')
        self.get(url)
        self.logger.info(f'Navigated to {url}.\n')

    def upload_content(self, value, by, content_path):
        """
        This uploads content(via content's path) to an input. Unfortunately directory structures
        are not honored using non chrome.

        Args:
            value (str): The element search string.
            by (str): The method for applying the search string.
            content_path (str): The path of the content to upload.
        """
        self.logger.info('\n')
        self.logger.info(f'Uploading content {content_path} to element {value} by {by}.')

        self.execute_script(
            """
                const element = document.querySelectorAll(arguments[0])[0];
                element.style.display = "block";
            """, value)

        if self.platform_name == 'safari' and '.' not in content_path.split('/')[-1]:
            content_path += '\n'
        elif self.platform_name == 'firefox' and '.' not in content_path.split('/')[-1]:
            content_path = '\n'.join([file for file in iglob(f'{content_path}//**', recursive=True)
                                      if '.' in file.split('/')[-1]])

        try:
            self.find_element_explicitly(value, by).send_keys(content_path)
        except Exception as e:
            if self.platform_name != 'safari':
                self.logger.error(e)
                self.logger.error('\n')
                raise Exception(e)

        # WORKAROUND - lameness
        self.time.sleep(.5)
        self.logger.info(f'Uploaded content {content_path} to element {value} by {by}.\n')

    def wait_for_dialog_close(self, value=None, by=None, timeout=15):
        """
        This waits for the dialog to close before releasing.

        Args:
            value (None|str): The element search string.
            by (None|str): The method for applying the search string.
            timeout (int): The max time to check for a dialog change.
        """
        if not value:
            value, by = ['div[role="dialog"]', 'css selector']

        self.logger.info('\n')
        self.logger.info(f'Waiting for the dialog {by}: {value} to close.')

        timeout_ms = self.time.time() + timeout
        while self.time.time() <= timeout_ms:
            element = self.find_element_explicitly(value, by, safe=True, timeout=1)
            if not element:
                self.logger.info(f'Waited for the dialog {by}: {value} to close.\n')
                return

        error_message = f'Waited {timeout} seconds and the dialog {by}: {value} never closed.'
        self.logger.error(error_message)
        self.logger.error('\n')
        raise self.driver_exceptions.TimeoutException(error_message)

    def copy_element_highlighted_text(self, element):
        """
        This highlights an element with highlightable text using hotkeys.

        Args:
            element (WebElement): The element to highlight content from.

        Returns:
            copied_text (str): The text copied to the clipboard.
        """
        self.logger.info('\n')
        self.logger.info('Copying the text from the element.')

        h, w, x, y = list(element.rect.values())

        ac = self.action_chains(self)
        ac.reset_actions()
        ac.drag_and_drop_by_offset(element, -w / 2, -h / 2).click(). \
            drag_and_drop_by_offset(None, 0, h / 2).perform()

        pya.hotkey('command', 'shift', 'down', interval=.5)
        self.time.sleep(.5)
        pya.hotkey('command', 'c', interval=.5)

        copied_text = pyperclip.paste()

        self.logger.info(f'Copied the text {copied_text} from the element.\n')
        return str(copied_text)

    def switch_to_iframe(self, value='iframe', by='css selector'):
        """
        This switches context to an iframe.

        Args:
            value (str): The iframe search string.
            by (str): The method for applying the search string.
        """
        self.logger.info('\n')
        self.logger.info(f'Switching to the iframe with value: {value} and by: {by}.')

        timeout_ms = self.time.time() + 10
        while self.time.time() <= timeout_ms:
            try:
                self.switch_to.default_content()
                self.switch_to.frame(self.find_element_explicitly(value, by))
            except:
                self.time.sleep(1)

        self.logger.info(f'Switched to the iframe with value: {value} and by: {by}.\n')

    def capture_specific_element_screenshot(self, element, path):
        """
        This captures screenshot of specific webelement  and copy it in specific location.

        Args:
            element(WebElement): The element whose screenshot needs to be taken.
            path(str): path of file where to store the  screenshot of image.
        """
        self.logger.info('\n')
        self.logger.info(f'Capturing screenshot of specific webelement {element} at {path}.')
        element.screenshot(path)
        self.logger.info(f'Captured screenshot of specific webelement {element} at {path}.\n')
