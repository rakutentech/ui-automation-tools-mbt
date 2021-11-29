import os
import shutil
import importlib
from glob import iglob

import uiautomationtools.models.model_conversion as mc
import uiautomationtools.helpers.string_helpers as sh
import uiautomationtools.helpers.directory_helpers as dh


class PytestHelper(object):
    app = None
    PARAMS = {}
    skipped_steps = []
    skip_validations = False
    store = {}

    root_dir = None
    app_dir = None
    calling_test = None
    test_path = str(root_dir) + str(calling_test)
    test_data = None
    credentials = {}
    model_steps = None
    selectors = {}
    new_steps = True
    decision_map = None

    def setup_class(self):
        """
        Setup that runs before any 'test_' methods.
        """
        self.root_dir = self.root_dir or dh.get_root_dir()
        self.app_dir = dh.get_src_app_dir()
        self.calling_test = self.calling_test or os.environ.get('PYTEST_CURRENT_TEST').split('::')[0]
        if 'None' in self.test_path:
            self.test_path = f"{self.root_dir}/{self.calling_test}"

        self.test_data = f"{self.root_dir}/tests/{self.app_dir}/data/"

        files = iglob(f'{self.root_dir}/credentials//**', recursive=True)
        if not self.credentials:
            self.credentials = {os.path.basename(f).split('.')[0]: dh.load_json(f)
                                for f in files if os.path.basename(f)}

        model_name = self.calling_test.split('/')[-1].split('.')[0]
        self.model_steps = self.model_steps or mc.prepare_steps(model_name, self.new_steps, self.decision_map)
        self.original_model_steps = self.model_steps[:] # deepcopy if doesnt work

        if self.skip_validations:
            self.model_steps = [s for s in self.model_steps if not s['name'].startswith('v_')]

        if self.skipped_steps:
            filtered_models = []
            for step in self.model_steps:
                if any(ancestor in self.skipped_steps for ancestor in step.get('ancestors', [])):
                    continue
                if any(name in self.skipped_steps for name in step.get('name', [])):
                    continue
                filtered_models.append(step)
            self.model_steps = filtered_models
        if not self.model_steps:
            raise Exception("No model steps were generated - check the model drawio and json files. "
                            "If the issue seems unexplainable, don't try to fix it - in new drawio files, "
                            "just redraw the model and it's imports.")

    def teardown_class(self):
        """
        Teardown that runs after 'test_' methods.
        """
        if self.app.driver.custom_proxy and self.app.driver.custom_proxy.process.poll() is None:
            self.app.driver.proxy_dump.stop_proxy_dump()
        for store in self.store.values():
            store['app'].driver.quit()

    def test_run_steps(self, test_app, target):
        """
        This iterates through and runs the model steps.

        Args:
            target (str): The pytest target command line param (can set in pytest.ini).
        """
        if not self.app:
            raise Exception('No app driver detected!')

        self.store[target] = {'app': self.app, 'steps_completed': [],
                              'step_pass': [False], 'traceback': None,
                              'logs_path': self.app.driver.logging.log_file_path}

        current_test_module = ''
        my_class = None

        py_test_path = f'{self.root_dir}/tests/{self.app_dir}'
        all_test_paths = [py_test for py_test in iglob(f'{py_test_path}//**', recursive=True)
                          if py_test.split('.')[-1] == 'py']

        if PytestHelper.model_steps:
            self.model_steps = PytestHelper.model_steps

        for step in self.model_steps:
            self.store[target]['step_pass'][-1] = False

            actions = step.get('actions')
            if actions:
                self.PARAMS.update(actions)

            test_module = step['modelName']
            if not step.get('ancestors'):
                test_module = 'self'
            step_name = step['name']

            try:
                if test_module == 'self' or test_module == self.test_path.split('/')[-1]:
                    eval(f"self.{step_name}()")
                else:
                    if test_module != current_test_module:
                        test_path = dh.find_reference_in_list(f'{test_module}.py', all_test_paths)
                        test_module_path = '.'.join(test_path.replace(self.root_dir, '').split('/')[1:-1])

                        module = importlib.import_module(f"{test_module_path}.{test_module}")
                        class_name = sh.delimiter_to_camelcase(test_module)
                        my_class = getattr(module, class_name)
                        current_test_module = test_module

                    method_name = my_class.__dict__.get(step_name)
                    if not method_name:
                        my_class.PARAMS.update(self.PARAMS)
                        method_name = my_class.__dict__.get(step_name)
                    method_name(self)

                self.store[target]['steps_completed'].append(step)
                self.store[target]['step_pass'][-1] = True
            except Exception as e:
                fail_path = self.store[target]['logs_path'].replace('/pass/', '/fail/')
                self.app.driver.logger.error(e, exc_info=True)
                shutil.move(self.store[target]['logs_path'], fail_path)
                raise Exception(e)
