import os
import re
import logging
from datetime import datetime
import uiautomationtools.helpers.directory_helpers as dh


class Logger(object):
    """
    This is a wrapper around the logging module.
    """
    def __init__(self):
        """
        This is the constructor for Logging.
        """
        self.logger = logging
        self.root_dir = dh.get_root_dir()
        self.log_dir = None
        self.log_file_path = self.set_logger()
        self.set_logger_handler(filename=self.log_file_path)

    def set_logger(self, by_time=False):
        """
        This sets up the logging directories and file paths.

        Args:
            by_time (bool): Whether to keep all successive runs by time.

        Returns:
            log_file_path: The path of the log file to write to.
        """
        calling_test = os.environ.get('PYTEST_CURRENT_TEST')
        target = re.findall(r'\[(.*?)\]', calling_test) or ['']
        target = target[0]
        file_path = f"{self.root_dir}/{calling_test.split('::')[0].replace('test_', f'test_{target}_')}"
        file_path = file_path.replace('/tests/', f'/run_info/run_logs/{target}/')

        self.log_dir = '/'.join(file_path.split('/')[:-1])
        log_dir_path_pass = f'{self.log_dir}/pass'
        log_dir_path_fail = f'{self.log_dir}/fail'
        dh.safe_mkdirs(log_dir_path_pass)
        dh.safe_mkdirs(log_dir_path_fail)

        filename = re.sub(r'test_|.py', '', file_path.split('/')[-1])
        if by_time:
            filename += f"_{datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}"
        return f'{log_dir_path_pass}/{filename}.log'

    def set_logger_handler(self, **kwargs):
        """
        This (re)sets the logging handler.

        Args:
            kwargs: See the logging basicConfig function for more param details.

        Returns:
            logging: The updated logging module.
        """
        stock_kwargs = {'level': logging.INFO, 'filemode': 'w', 'filename': 'stock_log_file.log',
                        'format': '%(asctime)s | %(levelname)s |  %(name)s | %(message)s'}
        stock_kwargs.update(kwargs)

        self.logger.root.handlers = []
        self.logger._handlerList = []
        self.logger.basicConfig(**stock_kwargs)
