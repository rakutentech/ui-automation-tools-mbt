# Web and mobile automated testing using a model based approach in Python
This provides a starting point for automating web and mobile applications in Python using the pytest 
framework. The tests are documented as drawio flow diagrams of action and validation steps.

## Required dependencies
1. `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"` **(selenium, appium)**
2. `brew tap AdoptOpenJDK/openjdk && brew install --cask adoptopenjdk8` **(selenium, appium)**
3. `brew install usbmuxd --HEAD` **(appium)**
4. `brew install libimobiledevice --HEAD` **(appium)**
5. `brew install ideviceinstaller --HEAD` **(appium)**
6. `brew install carthage` **(appium)**
7. `brew install ios-webkit-debug-proxy` **(appium)**
8. `brew install mitmproxy` **(selenium, appium)**
9. `brew install wget` **(selenium, appium)**
10. `brew install pyenv` **(selenium, appium)**
11. `PYTHON_CONFIGURE_OPTS="--enable-framework" pyenv install 3.8.10 && pyenv global 3.8.10 && echo export PATH="$(pyenv root)/shims:$PATH" >> ~/.bash_profile && . ~/.bash_profile && pip install pipenv` **(selenium, appium)**
12. `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.35.1/install.sh | bash && . ~/.bash_profile && nvm install --lts` **(appium)**
13. `npm install -g appium` **(appium)**
14. `npm install -g appium-doctor` **(appium)**
15. [graphwalker-cli](https://altom.gitlab.io/altwalker/altwalker/installation.html) **(selenium, appium)**
16. [chrome](https://chromedriver.chromium.org) and/or [geckodriver](https://github.com/mozilla/geckodriver/releases) **(selenium, _appium_)**

## Setup
1. Clone this repo
2. In the terminal cd into the root of your main test project
3. In the terminal run `pipenv install -e path_to_uiautomationtools`

## Usage
### Helpers
```
import uiautomationtools.helpers.decorator_helpers as dh
import uiautomationtools.helpers.dictionary_helpers as dh
import uiautomationtools.helpers.directory_helpers as dh
import uiautomationtools.helpers.list_helpers as ls
import uiautomationtools.helpers.string_helpers as sh
```

### Pytest
This class contains all the model reading and execution functionality - a proper test model is required. 
There are class properties that can be set from your SomeBasePytest class. You can also add your own test
methods that will run before executing the test model steps. The **target** is either a browser or mobile
device configurable through a pytest.ini. 
```
import pytest
from uiautomationtools.pytest import PytestHelper

class SomeBasePytest(PytestHelper):

    @pytest.fixture
    def test_app(self, target):
        self.app = PytestHelper.app = App(...)
```

### Selenium and Appium
Custom selenium actions in addition to the standard methods and properties.
```
from uiautomationtools.selenium import SeleniumExtended

driver = SeleniumExtended(browser=browser)
element = driver.find_element_explicitly('button#buttonId', 'css selector')
```
Custom appium actions in addition to the standard methods and properties. Depending on the 
platform specified in the desired capabilities, an android or ios driver will be returned.
```
from uiautomationtools.selenium import appium_factory

driver = appium_factory('http://localhost:4723/wd/hub', desired_capabilities)
element = driver.find_element_explicitly('//android.widget.TextView[@content-desc="something"]', 'xpath')
```

### Validations
This class validates dom scrapes and computes a list of mismatch dictionaries.
```
from uiautomationtools.validations import Validations

validations = Validations(driver)
refs = validations.build_references_selenium()
driver.refresh()
mismatches = validations.validate_references(stored_references=refs)
mismatches => [{'key': 'class', 'd1': 'pre_refresh', 'd2': 'post_refresh'}, ...]
```

### Directory structure
This package requires the following base structure for the project.
```
.
├── credentials                         # Optional - credentials
│   └── credentials.json                # Optional - credentials as json
├── drivers                             # Required - webdrivers
│   └── {platform}_chromedriver         # Required - darwin_chromedriver, darwin_geckodriver (firefox), etc
├── src                                 # Required - source code
│   └── app                             # Required - app under test (page objects/API's)
│       ├── ...                         # Required - app framework code
│       └── selectors                   # Required - selectors
│           └── selectors.py            # Required - selectors as a dictionary
├── tests                               # Required - test files
│   ├── data                            # Optional - test data
│   │   └── data.json                   # Optional - test data as json
│   └── app                             # Required - app under test (same name as /src/app)
│       ├── models                      # Required - test models
│       │   └── feature                 # Optional - feature of test models
│       │       └── test_file.drawio    # Required - test model as .drawio
│       └── ui_automation               # Required - test code
│           └── feature                 # Optional - feature of test code
│               └── test_file.py        # Required - pytest test (same name as the corresponding model file)
└── validations                         # Optional - validation data
    └── feature                         # Optional - feature of validations
        └── test_file.json              # Optional - validation data as json (same name as the corresponding model file)
```