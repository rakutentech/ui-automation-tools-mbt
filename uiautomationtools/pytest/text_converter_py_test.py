import os
import shutil
import sys
import json
import pytest
sys.path.append("..")

from uiautomationtools.models.text_converter import TextConverter, TextConverterException

base_test_path = './uiautomationtools/pytest'
test_path = f"{base_test_path}/tests/text_converter"
expected_data_path = f'{base_test_path}/expected_data/text_converter'

@pytest.mark.usefixtures("create_environment")
@pytest.mark.usefixtures("clean_environment")
class TestTextConverter:

    test_path = test_path
    expected_data_path = expected_data_path

    def test_text_converter_exist(self):
        text = TextConverter()
        assert type(text) == TextConverter

    def test_read_content(self):
        # Arrange
        # Act
        text = TextConverter()
        text.read_content(f'{self.test_path}/only_8_actions.txt')
        # Assert
        expected = 9
        assert expected == len(text.content)

    def test_process_content_OK(self):
        # Arrange
        # Act
        text = TextConverter()
        text.read_content(f'{self.test_path}/only_8_actions.txt')
        text.process_content()
        # Assert
        expected = 8
        assert expected == len(text.parsed_content)

    def test_process_content_OK_having_blank_lines(self):
        # Arrange
        # Act
        text = TextConverter()
        text.read_content(f'{self.test_path}/only_8_actions_with_blank_lines.txt')
        text.process_content()
        # Assert
        expected = 8
        assert expected == len(text.parsed_content)

    def test_process_content_FAIL_missing_start(self):
        # Arrange
        # Act
        text = TextConverter()
        text.read_content(f'{self.test_path}/no_start.txt')
        with pytest.raises(TextConverterException) as e:
            text.process_content()
        # Assert
        expected = f"The {self.test_path}/no_start.txt does not have 'Start' entry point format.\nCheck the example how test formats are supported"
        assert expected == str(e.value)

    def test_process_content_FAIL_empty_file(self):
        # Arrange
        # Act
        text = TextConverter()
        text.read_content(f'{self.test_path}/empty_file.txt')
        with pytest.raises(TextConverterException) as e:
            text.process_content()
        # Assert
        expected = f"The {self.test_path}/empty_file.txt does not have 'Start' entry point format.\nCheck the example how test formats are supported"
        assert expected == str(e.value)

    def test_process_content_FAIL_no_methods(self):
        # Arrange
        # Act
        text = TextConverter()
        text.read_content(f'{self.test_path}/no_methods.txt')
        with pytest.raises(TextConverterException) as e:
            text.process_content()
        # Assert
        expected = f"Error parsing file: {self.test_path}/no_methods.txt | No methods found."
        assert expected == str(e.value)

    def test_process_content_FAIL_missing_e_(self):
        # Arrange
        # Act
        text = TextConverter()
        text.read_content(f'{self.test_path}/only_actions_missing_e_.txt')
        with pytest.raises(TextConverterException) as e:
            text.process_content()
        # Assert
        expected = "Error parsing at line: 2 | Expected a method which starts with 'e_' or 'i_' but received the method: v_action1\n"
        assert expected == str(e.value)

    def test_process_content_FAIL_missing_v_middle(self):
        # Arrange
        # Act
        text = TextConverter()
        text.read_content(f'{self.test_path}/only_actions_missing_v_middle.txt')
        with pytest.raises(TextConverterException) as e:
            text.process_content()
        # Assert
        expected = "Error parsing at line: 5 | Expected a method which starts with 'v_' but received the method: e_action3\n"
        assert expected == str(e.value)

    def test_process_content_FAIL_missing_v_EOL(self):
        # Arrange
        # Act
        text = TextConverter()
        text.read_content(f'{self.test_path}/only_actions_missing_v_EOL.txt')
        with pytest.raises(TextConverterException) as e:
            text.process_content()
        # Assert
        expected = "Error parsing at line: 5 | Expected a method which starts with 'v_' but reached the end of the file (EOL)"
        assert expected == str(e.value)

    def test_process_content_FAIL_missing_i_(self):
        # Arrange
        # Act
        text = TextConverter()
        text.read_content(f'{self.test_path}/only_actions_missing_i_.txt')
        with pytest.raises(TextConverterException) as e:
            text.process_content()
        # Assert
        expected = "Error parsing at line: 2 | Expected a method which starts with 'e_' or 'i_' but received the method: iv_action1\n"
        assert expected == str(e.value)

    def test_process_content_FAIL_missing_iv_middle(self):
        # Arrange
        # Act
        text = TextConverter()
        text.read_content(f'{self.test_path}/only_actions_missing_iv_middle.txt')
        with pytest.raises(TextConverterException) as e:
            text.process_content()
        # Assert
        expected = "Error parsing at line: 5 | Expected a method which starts with 'iv_' but received the method: i_action3\n"
        assert expected == str(e.value)

    def test_process_content_FAIL_missing_iv_EOL(self):
        # Arrange
        # Act
        text = TextConverter()
        text.read_content(f'{self.test_path}/only_actions_missing_iv_EOL.txt')
        with pytest.raises(TextConverterException) as e:
            text.process_content()
        # Assert
        expected = "Error parsing at line: 5 | Expected a method which starts with 'iv_' but reached the end of the file (EOL)"
        assert expected == str(e.value)

    def test_convert_to_JSON(self):
        # Arrange
        test_name = "only_8_actions"
        # Act
        text = TextConverter(debug=True)
        text.convert_to_JSON(f'{self.test_path}/{test_name}.txt')
        # Assert
        with open(f'{expected_data_path}/{test_name}.json') as expected_file, open(f'{self.test_path}/{test_name}.json') as current_file:
            expected = json.load(expected_file)
            current = json.load(current_file)
        assert expected == current

    def test_convert_to_JSON_with_inline_params(self):
        # Arrange
        test_name = "only_8_actions_with_inline_params"
        # Act
        text = TextConverter(debug=True)
        text.convert_to_JSON(f'{self.test_path}/{test_name}.txt')
        # Assert
        with open(f'{expected_data_path}/{test_name}.json') as expected_file, open(f'{self.test_path}/{test_name}.json') as current_file:
            expected = json.load(expected_file)
            current = json.load(current_file)
        assert expected == current

    def test_convert_to_JSON_OK_with_lines_params(self):
        # Arrange
        test_name = "only_8_actions_with_lines_params"
        # Act
        text = TextConverter(debug=True)
        text.convert_to_JSON(f'{self.test_path}/{test_name}.txt')
        # Assert
        with open(f'{expected_data_path}/{test_name}.json') as expected_file, open(f'{self.test_path}/{test_name}.json') as current_file:
            expected = json.load(expected_file)
            current = json.load(current_file)
        assert expected == current

    def test_convert_to_JSON_FAIL_missing_params(self):
        # Arrange
        test_name = "only_8_actions_missing_inline_params"
        # Act
        text = TextConverter(debug=True)
        with pytest.raises(TextConverterException) as e:
            text.convert_to_JSON(f'{self.test_path}/{test_name}.txt')
        # Assert
        expected = "Error parsing at line: 4 | Expected a method with parameters. If not, do not use the '/' at the end of the line"
        assert expected == str(e.value)


@pytest.fixture(scope="module")
def clean_environment():
    shutil.rmtree(test_path, ignore_errors=True)


@pytest.fixture(scope="module")
def create_environment():
    test_data = f'{base_test_path}/tests_data/text_converter/'
    if not os.path.exists(test_data):
        raise Exception("Invalid test environment to be used in the test")
    shutil.copytree(test_data, test_path)
