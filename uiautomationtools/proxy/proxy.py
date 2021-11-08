import os
import subprocess
from mitmproxy import io
from datetime import datetime

import uiautomationtools.helpers.json_helpers as jh
import uiautomationtools.helpers.directory_helpers as dh


class Proxy(object):
    """
    This class starts a proxy and writes data to a dump file.
    """

    def __init__(self, path):
        """
        The constructor of Proxy.

        Args:
            path (str): The path of the dump file.
        """
        self.path = path
        self.process = None
        self.processes = []
        self.dump_history = []

    def start_proxy_dump(self, filters=None):
        """
        This starts the proxy and creates the dump file.

        Args:
            filters (str): Additional data filters to apply when writing to the dump file.
        """
        filters = filters or ''
        date = datetime.now().strftime('%y-%m-%d_%H-%M-%S')
        dirname = os.path.dirname(self.path)
        basename = os.path.basename(self.path).replace('.', f'_{date}.')
        self.path = f'{dirname}/{basename}'
        dh.safe_mkdirs(dirname)

        self.process = subprocess.Popen(f'mitmdump -w {self.path} --anticomp {filters}', shell=True)
        self.processes.append(self.process)

    def stop_proxy_dump(self):
        """
        This kills the proxy.
        """
        for p in self.processes:
            p.kill()

    def get_proxy_data(self):
        """
        This gets all the proxy data.

        Returns:
            data (list): The proxy data.
        """
        def _worker(state):
            request = state.get('request', None)
            response = state.get('response', None)

            if request:
                for k, v in request.items():
                    v_type = type(v)
                    if v_type is str or v_type is bytes:
                        request[k] = jh.deserialize(v, UnicodeDecodeError)
            if response:
                for k, v in response.items():
                    v_type = type(v)
                    if v_type is str or v_type is bytes:
                        response[k] = jh.deserialize(v, UnicodeDecodeError)

            return {'request': request, 'response': response}

        with open(self.path, "rb") as logfile:
            freader = io.FlowReader(logfile)
            self.dump_history = [_worker(f.get_state()) for f in freader.stream()]
            return self.dump_history

    def get_recent_proxy_data(self):
        """
        This gets recently (not in self.dump_history) recorded data.

         Returns:
            data (list): The recent proxy data.
         """
        history_length = len(self.dump_history)
        return self.get_proxy_data()[history_length:]
