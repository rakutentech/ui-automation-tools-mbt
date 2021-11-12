import os
import re
from glob import iglob
from datetime import datetime
from bs4 import BeautifulSoup

import uiautomationtools.helpers.dictionary_helpers as dict_helpers
import uiautomationtools.helpers.directory_helpers as dir_helpers


class Validations(object):
    """
    This class holds all the ways we gather and use information for validations.
    """

    def __init__(self, driver, debug=False):
        """
        The constructor for Validations.

        Args:
            driver (webdriver): A selenium/appium webdriver.
            debug (bool): Whether to run in debug mode.
        """
        self.driver = driver
        self.debug = debug
        self.logger = self.driver.logger
        self.dict_helpers = dict_helpers

        self.references_directory = None
        self.references_file_paths = None
        self.update_reference_paths()
        self.skipped_keys = ['write_time', 'reference_name', 'bounds']

    def update_reference_paths(self):
        app_dir = dir_helpers.get_src_app_dir()
        self.references_directory = f'{dir_helpers.get_root_dir()}/validations/' \
                                    f'{app_dir}/{self.driver.platform_name}'
        self.references_file_paths = [ref for ref in iglob(f'{self.references_directory}//**', recursive=True)
                                      if '.json' in ref]

    def _write_json(self, references, file_path=None):
        """
        This will write the scraped references to a json file named 'reference_name' at the store path.

        Args:
            references (dict): The scraped elements from a page.
            file_path (None|str): The file path where to write the build references.
        """
        if not file_path:
            return

        directory = os.path.dirname(file_path)
        dir_helpers.safe_mkdirs(directory)
        dir_helpers.make_json(references, file_path)
        self.references_file_paths.append(file_path)

    def _build_references(self, html, skipped_tags=None):
        """
        This is the worker for building references.

        Args:
            html (str): HTML of a page.
            skipped_tags (None|list): The element tags to skip.

        Returns:
            references (dict): The references of the page.
        """
        skipped_tags = skipped_tags or []

        references = {}
        for d in BeautifulSoup(html, 'html.parser').descendants:
            if 'Tag' not in str(type(d)):
                continue

            attrs = {k: v for k, v in d.attrs.items() if v}
            attr_class = attrs.get('class')
            if attr_class:
                attrs['class'] = ' '.join(attr_class)

            text = getattr(d, 'text', '')
            text = re.sub(r'\n+', '', text)
            if text:
                attrs['text'] = text

            if d.name:
                attrs['tag'] = d.name

            context = attrs.get('id') or attrs.get('name') or attrs.get('placeholder') or attrs.get('text') or 'no_key'
            context = re.sub(r'(\W|_)+', '_', context.lower())

            global_tags = f"{attrs.get('tag')},{attrs.get('class')},{context}"
            if skipped_tags and any(t in global_tags for t in skipped_tags):
                continue

            if not references.get(context):
                references[context] = [attrs]
            elif attrs not in references[context]:
                references[context].append(attrs)

        return references

    def build_references_appium(self, file_path=None, skipped_tags=None):
        """
        This builds appium ui references (things to validate) to compare against for a specific page
        and stores them (in a fixed location) in json.

        Args:
            file_path (None|str): The file path where to write the build references.
            skipped_tags (None|list): The element types to skip e.g. .Image or android.widget.Image etc.

        Returns:
            references (dict): The dictionary of the references.
        """
        self.logger.info(f'\n')
        self.logger.info(f'Building appium references for {file_path}.')
        html = self.driver.get_page_source()
        references = self._build_references(html, skipped_tags=skipped_tags)
        references['write_time'] = datetime.strftime(datetime.now(), '%Y-%m-%d_%H:%M:%S')
        self._write_json(references, file_path)
        self.update_reference_paths()
        self.logger.info(f'Built appium references for {file_path}.\n')
        return references

    def build_references_selenium(self, file_path=None, skipped_tags=None, html=None, **kwargs):
        """
        This builds selenium ui references (things to validate) to compare against for a specific page
        and stores them (in a fixed location) in json.

        Args:
            file_path (None|str): The file path where to write the build references.
            skipped_tags (None|list): The element types to skip e.g. div or ui etc.
            html (None|str): The html to build. If None then it builds from the page. To find specific html you can use
                             get_page_source(value, safe=True).
            kwargs:
                iframe (bool): Whether the references being built live in an iframe.
                body (bool): Whether the references being built live in the body.

        Returns:
            references (dict): The dictionary of the references.
        """
        self.logger.info(f'\n')
        self.logger.info(f'Building selenium references for {file_path}.')

        if not html:
            value = 'div'
            if kwargs.get('iframe'):
                self.driver.switch_to.default_content()
                iframe_element = self.driver.find_element_explicitly('iframe', 'css selector')
                self.driver.switch_to.frame(iframe_element)
            if kwargs.get('body'):
                value = 'body'
            html = self.driver.get_page_source(value=value, safe=True)
            if kwargs.get('iframe'):
                self.driver.switch_to.default_content()
        if not html:
            return {}

        references = self._build_references(html, skipped_tags=skipped_tags)
        references['write_time'] = datetime.strftime(datetime.now(), '%Y-%m-%d_%H:%M:%S')
        self._write_json(references, file_path)
        self.update_reference_paths()
        self.logger.info(f'Built selenium references for {file_path}.\n')
        return references

    def validate_references(self, reference_name=None, stored_references=None, safe=False, skipped_keys=None,
                            skipped_tags=None, normalize=False, html=None, **kwargs):
        """
        This compares stored references of the same name with current ones.

        Args:
            reference_name (None|str): The name of the screen.
            stored_references (None|dict): Passed values to compare against
            safe (bool): Whether to raise errors on elements not found.
            skipped_keys (None|list): The keys to skip in the comparison.
            skipped_tags (None|list): The element tags to skip.
            normalize (bool): Whether to convert each of the comparable values in the same casing.
            html (None|str): The html to build. If None then it builds from the page.
            kwargs:
                iframe (bool): Whether the references being build live in an iframe.
                body (bool): Whether the references being built live in the body.

        Returns:
            mismatches (dict): A record of any mismatching keys and or values.
        """
        self.logger.info(f'\n')
        self.logger.info(f'Validating references for {reference_name}.')
        skipped_keys = skipped_keys or []
        skipped_keys.extend(self.skipped_keys)

        if not stored_references:
            if reference_name:
                reference_name = f"{reference_name.split('.')[0]}.json"
            reference_path = dir_helpers.find_reference_in_list(reference_name, self.references_file_paths)
            stored_references = dir_helpers.load_json(reference_path)

        if 'native' in self.driver.context.lower():
            current_references = self.build_references_appium(skipped_tags=skipped_tags)
        else:
            current_references = self.build_references_selenium(skipped_tags=skipped_tags, html=html, **kwargs)

        mismatches = self.dict_helpers.async_compare_dictionaries(stored_references, current_references,
                                                                  skipped_keys, normalize)
        if (mismatches.get('keys') or mismatches.get('values')) and not safe:
            error_message = f'Validated references with mismatches {mismatches}.'
            self.fail(error_message)

        self.logger.info(f'Validated references for {reference_name}.\n')
        return mismatches

    def fail(self, error_message, exception=Exception):
        """
        This fails a test. To enable debug mode set the property self.debug to True.

        Args:
            error_message (str): The failure message to log.
            exception (exception): The exception to raise.
        """
        self.logger.error(error_message)
        if not self.debug:
            raise exception(error_message)
        else:
            try:
                raise exception(error_message)
            except exception:
                self.logger.error('Debugging the raise.\n')

    def existence_validation(self, soft_checks_list=None, iframe=False, message=None):
        """
        This softly checks for existence within a dom.

        Args:
            soft_checks_list (None|list):  List of soft check items to be validated on specific page.
            iframe (bool): Whether to do a soft check inside iframe tag.
            message (str): A custom error message to log.

        Returns:
           data (dict): The dictionary of references if it exists for the properly loaded pages.
        """
        self.logger.info(f'\n')
        self.logger.info(f'Checking {soft_checks_list} for existence.')
        soft_checks_list = soft_checks_list or []
        data = self.build_references_selenium(iframe=iframe)
        str_data = str(data)
        for s in soft_checks_list:
            if s not in str_data:
                message = message or f'The check for {s} not in the data.'
                self.fail(message)
        self.logger.info(f'Checked {soft_checks_list} for existence.\n')
        return data
