import os
import shutil
from glob import iglob
from subprocess import run
from subprocess import Popen

from uiautomationtools.selenium.appium.appium_shared import AppiumShared


class AppiumAndroid(AppiumShared):
    """
    This is an extension of AppiumShared containing android only methods.
    """
    def __init__(self, command_executor='http://127.0.0.1:4723/wd/hub', desired_capabilities=None, proxy=None,
                 keep_alive=True, direct_connection=False, session_id=None, language='en'):
        """
        This is the constructor for AppiumAndroid.

        Args:
            command_executor (str): Either a string representing URL of the remote server or a custom
                                    remote_connection.RemoteConnection object.
                                    Defaults to 'http://127.0.0.1:4444/wd/hub'.
            desired_capabilities (dict): A dictionary of capabilities to request when starting the browser session.
            proxy (None|str): A selenium.webdriver.common.proxy.Proxy object. The browser session will be started
                              with given proxy settings, if possible.
            keep_alive (bool): Whether to configure remote_connection.RemoteConnection to use HTTP keep-alive.
            direct_connection (bool): Whether to honor keep_alive.
            session_id (str): The id of an existing session to connect to.
            language (str): The language of the selectors.
        """
        super().__init__(command_executor, desired_capabilities, proxy, keep_alive,
                         direct_connection, session_id, language)

    def get_backup(self, cwd=None, clean=True):
        """
        This gets the backup of an android device and unzips it.

        Args:
            cwd (None|str): The directory to use for writing the backup and unzip
            clean (bool): Whether to delete the files after unzipping.

        Returns:
            files (list): The files of whatever is unzipped.
        """
        cwd = cwd or '/'.join(self.logging.log_file_path.split('/')[:-4])
        self.logger.info('\n')
        self.logger.info('Generating backup.')

        backup = cwd + '/backup.ab'
        apps = cwd + '/apps'

        Popen(f'adb backup -noapk {self.current_package}', shell=True, cwd=cwd)
        self.find_element_explicitly(self.selectors['button_text'].format('BACK UP MY DATA')).click()
        self.find_element_explicitly('//android.view.View', timeout=30)
        self.time.sleep(5)

        Popen(r"(printf '\x1f\x8b\x08\x00\x00\x00\x00\x00' ; tail -c +25 backup.ab) | tar xfvz -", shell=True, cwd=cwd)
        self.time.sleep(5)

        files = [f for f in iglob(cwd + '/apps//**', recursive=True) if not os.path.isdir(f)]

        if clean:
            os.remove(backup)
            shutil.rmtree(apps)

        self.logger.info(f'Generated backup {files}.\n')
        return files

    def disable_network(self):
        """
        This function will disable mobile network on phone.
        """
        self.logger.info('\n')
        self.logger.info(f'Disabling mobile network.')
        run('adb shell svc wifi disable && adb shell svc data disable', shell=True)
        self.time.sleep(6)
        self.logger.info(f'Disabled mobile network.\n')

    def enable_network(self):
        """
        This function will enable mobile network on device using adb commands.
        """
        self.logger.info('\n')
        self.logger.info(f'Enabling mobile network.')
        run('adb shell svc wifi enable && adb shell svc data enable', shell=True)
        self.time.sleep(6)
        self.logger.info(f'Enabled mobile network.\n')

    def set_location_permission(self, on=True):
        """
        This function grant/revoke the location permission.

        Args:
            on (bool): Grant/revoke the location permission.
        """
        current_activity = self.current_activity
        package = self.current_package
        action = {True: 'grant', False: 'revoke'}[on]
        self.logger.info('\n')
        self.logger.info(f'Toggling location permissions {on}.')

        run(f'adb shell pm {action} {package} android.permission.ACCESS_FINE_LOCATION', shell=True)
        run(f'adb shell pm {action} {package} android.permission.ACCESS_COARSE_LOCATION', shell=True)

        self.logger.info(f'Toggled location permissions {on}.\n')
        if current_activity != self.current_activity:
            self.activate_app(package)

    def restart_device(self, timeout=90, safe=False):
        """
        This restarts the device.

        Args:
            timeout (int): The time in seconds to wait for the device to restart.
            safe (bool): Whether to raise an error for not restarting within the timeout.
        """
        self.logger.info('\n')
        self.logger.info(f'Restarting the device within {timeout} seconds.')
        run('adb reboot -p', shell=True)

        timeout_ms = self.time.time() + timeout
        while self.time.time() <= timeout_ms:
            try:
                self.current_activity
                self.desired_capabilities['noReset'] = True
                self.desired_capabilities['fullReset'] = False
                self.__init__(desired_capabilities=self.desired_capabilities)
                self.desired_capabilities.pop('noReset')
                self.desired_capabilities.pop('fullReset')
                self.logger.info(f'Restarted the device within {timeout} seconds.\n')
                return
            except:
                self.time.sleep(1)
                continue

        if not safe:
            error_message = f'Unable to restart device within {timeout} seconds.\n'
            self.logger.error(error_message)
            raise error_message

        self.logger.warning(f'Unable to restart device within {timeout} seconds.\n')
