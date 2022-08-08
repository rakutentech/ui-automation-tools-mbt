from glob import iglob
from typing import List
import os
import json
from uiautomationtools.models.model_conversion import generate_steps, step_expander
import uiautomationtools.helpers.directory_helpers as dh


class CodeGeneratorException(Exception):
    """Exception when error occurs while generating the class code."""


class CodeGenerator():

    def __init__(self, app: str):
        """
        Init method.

        Args:
            app: The app under test.
        """
        if not app or app == "":
            raise CodeGeneratorException("Error: Missing the app under test name. Please include the app under test name.")

        self.app = app
        self.root = f'{dh.get_root_dir()}/tests/{self.app}'
        self.models_dir = f'{self.root}/models'
        self.steps_dir = f'{self.root}/steps'
        self.ui_automation_dir = f'{self.root}/ui_automation'

    def get_model_path_from_model_name(self, model_name: str) -> str:
        """
        Return the path for the selected model_name.
        Raise a CodeGeneratorException error when model is not found or multiple models with same name.

        Args:
            model_name: The model name.
        """
        model_name_ext = model_name
        if not model_name_ext.endswith(".drawio"):
            model_name_ext += ".drawio"

        path = self.get_model(model_name_ext)
        if len(path) < 1:
            raise CodeGeneratorException(f'Model: {model_name_ext} not found')
        elif len(path) > 1:
            raise CodeGeneratorException(f'Model: {model_name_ext} found {len(path)} occurences. Please name the files unique.')

        return path[0]

    def build(self):
        """
        Generates the empty test classes for models without test class.
        """
        def compare(e):
            return (len(e.split(os.sep)))

        models = sorted(self.get_orphan_test_cases(), key=compare, reverse=True)

        steps = []
        while len(models) > 0:
            test_classes = {}
            model = models[0]

            steps = generate_steps(model_name=model.split(os.sep)[-1], new_steps=True, app_dir=self.app)
            steps = step_expander(steps, app_dir=self.app)
            # steps = [step for step in steps if step['name'].startswith('e_') or step['name'].startswith('v_')]

            for step in steps:
                if step['modelName'] in test_classes.keys():
                    if step['name'].startswith('e_') or step['name'].startswith('v_'):
                        test_classes[step['modelName']].add(step['name'])
                else:
                    test_classes[step['modelName']] = set()
                    if step['name'].startswith('e_') or step['name'].startswith('v_'):
                        test_classes[step['modelName']].add(step['name'])

            for model, methods in test_classes.items():
                self.create_test_class_file(model, methods)
            models = sorted(self.get_orphan_test_cases(), key=compare, reverse=True)

    def create_test_class_file(self, test_model: str, test_methods: List[str]):
        """
        Generates the test classes.

        Args:
            test_model: The path to the model draw.io file.
            test_methods: The methods to be included in the class.
        """
        import_ = "from src.infrastructure.appium.appium_base_pytest import AppiumBasePytest"
        class_name = "class {0}(AppiumBasePytest):"
        ident = "    "
        method_template = f'{ident}def {{0}}(self):\n{ident}{ident}raise NotImplementedError("The {{0}} method has not been implemented yet.")\n\n'
        empty_class_body = f"{ident}pass"

        filename_no_ext = os.path.splitext(os.path.basename(test_model))[0]
        testclass_filename = self.get_model_path_from_model_name(test_model).replace("/models/", "/ui_automation/").replace(".drawio", ".py")
        dirname = os.path.dirname(testclass_filename)

        if not os.path.exists(dirname):
            os.makedirs(dirname)

        if not os.path.exists(f"{dirname}/__init__.py"):
            open(f"{dirname}/__init__.py", "w").close()

        # TODO If class already exists, just add the new methods
        if os.path.exists(testclass_filename):
            return

        with open(testclass_filename, "w") as file:
            file.write(import_)
            file.write("\n\n\n")
            file.write(class_name.format(self.get_test_class_name(filename_no_ext)))
            file.write("\n")
            if len(test_methods) == 0:
                file.write(empty_class_body)
            else:
                for method in test_methods:
                    file.write(method_template.format(method))

    def get_test_class_name(self, filename_no_ext: str) -> str:
        """
        Returns the test class name in the expected format.

        Args:
            filename_no_ext: The filename without the extension.

        Returns:
            test_class_name: The test class name.
        """
        parts = [part for part in filename_no_ext.split("_") if len(part) > 0]
        return "".join([f"{part[0].upper()}{part[1:]}" for part in parts])

    def get_test_methods(self, filename: str) -> List[str]:
        """
        Gets all methods the test class requires to be implemented.

        Args:
            filename: The filename where the methods are listed.

        Returns:
            methods: The methods of the class. Can be empty.
        """
        filepath = f"{self.steps_dir}/{filename}"
        if not os.path.exists(filepath):
            raise CodeGeneratorException("The steps file is not found. Please check the model (draw.io) file is valid and the steps.json file has been properly generated")
        with open(filepath, "r") as file:
            data = json.load(file)
        methods = []
        for method in data:
            if method['name'].startswith('e_') or method['name'].startswith('v_'):
                methods.append(method['name'])
        return methods

    def get_orphan_test_cases(self) -> List[str]:
        """
        Gets all the current orphan test cases which don't have a test class.

        Returns:
            orphan_files: The Orphan files. Can be empty.
        """
        models = self.get_models()
        test_classes = [os.path.splitext(os.path.basename(test))[0] for test in self.get_test_classes()]
        orphan_tests = [model for model in models if not os.path.splitext(os.path.basename(model))[0] in test_classes]
        [print(model) for model in models if not os.path.splitext(os.path.basename(model)) in test_classes]
        return orphan_tests

    def get_model(self, model_name: str) -> List[str]:
        """_summary_

        Args:
            model_name (str): _description_

        Returns:
            List[str]: _description_
        """
        matching = [model for model in self.get_models() if model.endswith(model_name)]
        return matching

    def get_models(self) -> List[str]:
        """
        Gets all the models.

        Returns:
            models (list<str>): The models of the repo. Can be empty.
        """
        return [file for file in self.get_all_files_from_directory(self.models_dir) if file.endswith('.drawio')]

    def get_test_classes(self) -> List[str]:
        """
        Gets all the test classes.

        Returns:
            test_classes_files (list<str>): The test_classes_files of the repo. Can be empty.
        """
        return [file for file in self.get_all_files_from_directory(self.ui_automation_dir) if file.endswith('.py')]

    def get_all_files_from_directory(self, directory: str) -> List[str]:
        """
        Gets all the files available in the directory.

        Args:
            directory (str): The directory to search.

        Returns:
            methods (list<str>): The list with available files.
        """
        return [model for model in iglob(f'{directory}/**', recursive=True)]


def create_empty_test_class_models(app_dir: str):
    """
    Creates all the missing test classes the test model requires.

    Args:
        model_name (str): The model name.
        app_dir (str): App under test folder's name.
    """

    code = CodeGenerator(app=app_dir)
    code.build()
