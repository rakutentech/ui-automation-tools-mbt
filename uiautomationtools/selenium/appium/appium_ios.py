from uiautomationtools.selenium.appium.appium_shared import AppiumShared


class AppiumIos(AppiumShared):
    """
    This is an extension of AppiumShared containing ios only methods.
    """

    def __init__(self, command_executor='http://127.0.0.1:4723/wd/hub', desired_capabilities=None, proxy=None,
                 keep_alive=True, direct_connection=False, session_id=None, language='en'):
        """
        This is the constructor for AppiumIos.

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
        super().__init__(command_executor, desired_capabilities, proxy, keep_alive,
                         direct_connection, session_id, language)
