from appium import webdriver
from langdetect import detect
from appium.webdriver.common.touch_action import TouchAction

from uiautomationtools.selenium.selenium_appium_shared import SeleniumAppiumShared


class AppiumShared(webdriver.Remote, SeleniumAppiumShared):
    """
    This is an extension of the webdriver.remote and SeleniumAppiumShared classes.
    """
    def __init__(self, command_executor='http://127.0.0.1:4723/wd/hub', desired_capabilities=None, proxy=None,
                 keep_alive=True, direct_connection=False, session_id=None, language='en'):
        """
        This is the constructor for AppiumShared.

        Args:
            command_executor (str): Either a string representing URL of the remote server or a custom
                                    remote_connection.RemoteConnection object.
                                    Defaults to 'http://127.0.0.1:4444/wd/hub'.
            desired_capabilities (dict): A dictionary of capabilities to request when starting the browser session.
            proxy(None|str): A selenium.webdriver.common.proxy.Proxy object. The browser session will be started
                             with given proxy settings, if possible.
            keep_alive (bool): Whether to configure remote_connection.RemoteConnection to use HTTP keep-alive.
            direct_connection (bool): Whether to honor keep_alive.
            session_id (str): The id of an existing session to connect to.
            language (str): The language of the selectors.
        """
        if command_executor and session_id:
            self.attach_to_session(command_executor, session_id)
        else:
            webdriver.Remote.__init__(self, command_executor, desired_capabilities, None, proxy,
                                      keep_alive, direct_connection)
            SeleniumAppiumShared.__init__(self)

        self.update_settings({'normalizeTagNames': True})
        self.language = language
        self.android_bad_things = ['android.widget.ProgressBar']
        self.ios_bad_things = []

    def attach_to_session(self, command_executor, session_id):
        """
        This attaches to an existing session(device).

        Args:
            command_executor (str): The command executor url.
            session_id (str): The id of the session.

        Returns:
            self (AppiumShared): The updated class instance.
        """
        self.logger.info('\n')
        self.logger.info(f"Attaching to session {session_id} at {command_executor}.")
        original_execute = webdriver.Remote.execute

        def new_command_execute(new_self, command, params=None):
            if command == "newSession":
                return {'success': 0, 'value': None, 'sessionId': session_id}
            else:
                return original_execute(new_self, command, params)

        webdriver.Remote.execute = new_command_execute
        driver = webdriver.Remote(command_executor=command_executor, desired_capabilities={})
        driver.session_id = session_id
        webdriver.Remote.execute = original_execute

        self.__dict__.update(driver.__dict__)
        self.logger.info(f"Attached to session {session_id} at {command_executor}.\n")
        return self

    def switch_context(self, view=None):
        """
        This switches context ie from native app to webview.

        Args:
            view (None|str): The view you want ie native | chrome | etc. None is auto switch.
        """
        self.get_page_source(safe=True, timeout=15)

        orig_context = self.context
        self.logger.info('\n')
        if not view:
            self.logger.info(f'Switching from {orig_context} to {self.contexts[1]}.')
            self.switch_to.context(self.contexts[1])
        else:
            self.logger.info(f'Switching from {orig_context} to {view}.')
            next(self.switch_to.context(con) for con in self.contexts if view.lower() in con.lower())
        self.logger.info(f'Switched from {orig_context} to {view}.\n')

    def detect_language(self, text=None, limit=-1):
        """
        This detects the language of the passed text.

        Args:
            text (None|str): The text to check.
            limit (int): The length of chars of the text to check.

        Returns:
            language (str): The language found.
        """
        self.logger.info('\n')
        self.logger.info(f"Detecting the language for {text}.")
        if not text:
            all_text = self.selectors[self.platform_name]['all_text']
            elements = self.find_elements(all_text[-1], all_text[0]) + self.find_elements(all_text[-1], all_text[1])
            text = ''.join([element.text for element in elements if element.text])
        language = detect(text[:limit])
        self.logger.info(f"Detected the language {language} for {text}.\n")
        return language

    def get_page_source(self, **kwargs):
        """
        This is a wrapper for getting the page source via native or webview. Think of
        this as a supervised overload.

        Args:
            kwargs:
                timeout (int): The max time to check for a page change.
                safe (bool): Whether to raise errors on no new page source found.
                value (str): The element search string.
                by (str): The method for applying the search string.

        Returns:
            page_source (str): The page source for a probable new page or the inner
                                html of the fattest div on the page.
        """
        if 'native' in self.context.lower():
            return self.get_page_source_native(**kwargs)
        else:
            return super().get_page_source(**kwargs)

    def get_page_source_native(self, timeout=15, safe=False):
        """
        This waits for the page to be loaded before trying to get the page source.
        Note: If there is some new kinds of 'transition page/element/attribute add it to
              the bad things list below.

        Args:
            timeout (int): The max time to check for a page change.
            safe (bool): Whether to raise errors on no new page source found.

        Returns:
            page_source (str): The page source for a probable new page.
        """
        self.logger.info('\n')
        self.logger.info('Getting the native page source.')

        bad_things = self.android_bad_things
        if 'ios' in self.platform_name:
            bad_things = self.ios_bad_things

        timeout_ms = self.time.time() + timeout
        while self.time.time() <= timeout_ms:
            self.time.sleep(.25)
            page_source = self.page_source
            if page_source and not [thing for thing in bad_things if thing in page_source]:
                self.logger.info('Got the native page source.\n')
                return page_source

        if not safe:
            error_message = f'Unable to find the native page source within {timeout} seconds.\n'
            self.logger.error(error_message)
            raise self.driver_exceptions.NoSuchElementException(error_message)
        return ''

    def single_bidirectional_scroll(self, value, by='xpath', direction='down', step=.5, timeout=10, safe=False):
        """
        This moves distance of some step size of the height/width of the element in
        the directions down, up, left, or right.

        Args:
            value (str): The element search string.
            by (str): The method for applying the search string.
            direction (str): The direction to scroll (down, up, left, right)
            step (int|float): The step to move from the element.
            timeout (int): The max time to look for the anchor element.
            safe (bool): Whether to raise errors on scrolling out of bounds errors.
        """
        self.logger.info('\n')
        self.logger.info(f'Scrolling {direction} from {value}.')

        element = self.find_element_explicitly(value, by, safe=True, timeout=timeout)
        if not element:
            self.logger.info(f'No element {value} found to scroll from.\n')
            return

        x0 = element.location['x']
        y0 = element.location['y']
        height0 = element.size['height']
        width0 = element.size['width']

        actions = TouchAction(self)
        actions.press(x=x0, y=y0)
        actions.wait()

        if direction == 'down':
            actions.move_to(x=x0, y=y0 - step * height0)
        elif direction == 'up':
            actions.move_to(x=x0, y=y0 + step * height0)
        elif direction == 'right':
            actions.move_to(x=x0 - step * width0, y=y0)
        elif direction == 'left':
            actions.move_to(x=x0 + step * width0, y=y0)

        try:
            actions.release().perform()
        except Exception as e:
            if not safe:
                raise Exception(e)

        self.logger.info(f'Scrolled {direction} from {value}.\n')

    def restart_app(self):
        """
        This terminates and relaunches the app (no new install - same state).
        """
        app_package = self.capabilities['appPackage']
        self.logger.info('\n')
        self.logger.info(f'Restarting the app {app_package}.')

        # WORKAROUND - random 500ms timeout exceeded when terminating...
        try:
            self.terminate_app(app_package)
        except Exception as e:
            self.logger.warning(e)

        self.activate_app(app_package)
        self.time.sleep(3)
        self.logger.info(f'Restarted the app {app_package}.\n')

    def reinstall_app(self, fresh=True):
        """
        This uninstalls, re-installs, and relaunches the app.

        Args:
            fresh (bool): Whether to remove the existing app before re-installing.
        """
        fresh_log = {True: ' with fresh', False: ''}[fresh]

        self.logger.info('\n')
        self.logger.info(f'Reinstalling{fresh_log} and relaunching the app.')
        not fresh or self.remove_app(self.current_package)
        self.install_app(self.capabilities['app'])
        self.restart_app()
        self.logger.info(f'Reinstalled{fresh_log} and relaunching the app.\n')
