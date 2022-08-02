from glob import iglob
from typing import List
import os
import json
from uiautomationtools.models.model_conversion import generate_steps, step_expander
import uiautomationtools.helpers.directory_helpers as dh

class CodeGeneratorException(Exception):
    """Exception when error occurs while generating the class code."""

class CodeGenerator():

    __import = "from src.infrastructure.appium.appium_base_pytest import AppiumBasePytest"
    __className = "class {0}(AppiumBasePytest):"
    __ident = "    "
    __method = f'{__ident}def {{0}}(self):\n{__ident}{__ident}raise NotImplementedError("The {{0}} method has not been implemented yet.")\n\n'
    __emptyClass_body = f"{__ident}pass"


    def __init__(self, app: str):
        """
        Init method.

        Args:
            working_directory (str): The root path to the tests folder.
            app (str): The app under test.
        """
        if not app or app == "":
            raise CodeGeneratorException("Error: Missing the app under test name. Please include the app under test name.")
        self.app = app
        self.root = f'{dh.get_root_dir()}/tests/{self.app}'
        self.models_dir = f'{self.root}/models'
        self.steps_dir = f'{self.root}/steps'
        self.ui_automation_dir = f'{self.root}/ui_automation'

    def GetModelPathFromModelName(self, model_name: str) -> str:
        """
        Return the path for the selected model_name. 
        Returns a CodeGeneratorException error when model is not found or found multiple models with same name.

        Args:
            model_name (str): The model name.
        """
        model_name_ext = model_name
        if not model_name_ext.endswith(".drawio"):
            model_name_ext += ".drawio"
        path = self.GetModel(model_name_ext)
        if len(path) < 1:
            raise CodeGeneratorException(f'Model: {model_name_ext} not found')
        elif len(path) > 1:
            raise CodeGeneratorException(f'Model: {model_name_ext} found {len(path)} occurences. Please name the files unique.')
        
        return path[0]
        

    def Create(self, model_name:str):
        """
        Generate the test class.

        Args:
            model_name (str): The model name.
        """

        steps = generate_steps(model_name=model_name, new_steps=True, app_dir=self.app)
        steps = step_expander(steps, app_dir=self.app)
        steps = [step for step in steps if step['name'].startswith('e_') or step['name'].startswith('v_')]
        test_classes = {}
        for step in steps:
            if step['modelName'] in test_classes.keys() and not step['name'] in test_classes[step['modelName']]:
                # if step['name'].startswith('e_') or step['name'].startswith('v_'):
                test_classes[step['modelName']].append(step['name'])
            else:
                test_classes[step['modelName']] = [step['name']]

        for model, methods in test_classes.items():
            self.CreateTestClassFile(model, methods)

    def CreateTestClassFile(self, test_model: str, test_methods: List[str]):
        """
        Generates the test classes.

        Args:
            test_model (str): The path to the model draw.io file.
            test_methods (List[str]): The methods to be included in the class.
        """
        filename_no_ext = os.path.splitext(os.path.basename(test_model))[0]
        testclass_filename = self.GetModelPathFromModelName(test_model).replace("/models/", "/ui_automation/").replace(".drawio", ".py")
        dirname = os.path.dirname(testclass_filename)

        if not os.path.exists(dirname):
            os.makedirs(dirname)

        if not os.path.exists(f"{dirname}/__init__.py"):
            open(f"{dirname}/__init__.py", "w").close()
            
        # TODO If class already exists, just add the new methods
        if os.path.exists(testclass_filename):
            return

        with open(testclass_filename, "w") as file:
            file.write(self.__import)
            file.write("\n\n\n")
            file.write(self.__className.format(self.GetTestClassName(filename_no_ext)))
            file.write("\n")
            if len(test_methods) == 0:
                file.write(self.__emptyClass_body)
            else:
                for method in test_methods:
                    file.write(self.__method.format(method))


    def GetTestClassName(self, filename_no_ext: str) -> str:
        """
        Returns the test class name in the expected format.

        Args:
            filename_no_ext (str): The filename without the extension.
        
        Returns:
            test_class_name (str): The test class name.
        """
        parts = [part for part in filename_no_ext.split("_") if len(part) > 0]
        return "".join([f"{part[0].upper()}{part[1:]}" for part in parts])

    def GetTestMethods(self, filename: str) -> List[str]:
        """
        Gets all methods the test class requires to be implemented.

        Args:
            filename (str): The filename where the methods are listed.

        Returns:
            methods (list<str>): The methods of the class. Can be empty.
        """
        filepath = f"{self.steps_dir}/{filename}"
        if not os.path.exists(filepath):
            raise CodeGeneratorException(f"The steps file is not found. Please check the model (draw.io) file is valid and the steps.json file has been properly generated")
        with open(filepath, "r") as file:
            data = json.load(file)
        methods = []
        for method in data:
            if method['name'].startswith('e_') or method['name'].startswith('v_'):
                methods.append(method['name'])
        return methods

    def GetOrphanTestCases(self) -> List[str]:
        """
        Gets all the current orphan test cases which don't have a test class.

        Returns:
            orphan_files (list<str>): The Orphan files. Can be empty.
        """
        models = self.GetModels()
        test_classes = [os.path.splitext(os.path.basename(test))[0] for test in self.GetTestClasses()]
        orphan_tests = [model for model in models if not os.path.splitext(os.path.basename(model))[0] in test_classes]
        [print(model) for model in models if not os.path.splitext(os.path.basename(model)) in test_classes]
        return orphan_tests
    
    def GetModel(self, model_name: str) -> List[str]:
        """
        Gets the model path.

        Returns:
            matching (list<str>): The models of the repo. Can be empty.
        """
        matching = [model for model in self.GetModels() if model.endswith(model_name)]
        return matching

    def GetModels(self) -> List[str]:
        """
        Gets all the models.

        Returns:
            models (list<str>): The models of the repo. Can be empty.
        """
        return [file for file in self.GetAllFilesFromDirectory(self.models_dir) if file.endswith('.drawio')]
    
    def GetTestClasses(self) -> List[str]:
        """
        Gets all the test classes.

        Returns:
            test_classes_files (list<str>): The test_classes_files of the repo. Can be empty.
        """
        return [file for file in self.GetAllFilesFromDirectory(self.ui_automation_dir) if file.endswith('.py')]

    def GetAllFilesFromDirectory(self, directory: str) -> List[str]:
        """
        Gets all the files available in the directory.

        Args:
            directory (str): The directory to search.

        Returns:
            methods (list<str>): The list with available files.
        """
        return [model for model in iglob(f'{directory}/**', recursive=True)]


def create_empty_test_class_models(model_name: str, app_dir: str):
    """
    Creates all the missing test classes the test model requires.

    Args:
        model_name (str): The model name.
        app_dir (str): App under test folder's name.
    """

    code = CodeGenerator(app=app_dir)
    code.Create(model_name)
