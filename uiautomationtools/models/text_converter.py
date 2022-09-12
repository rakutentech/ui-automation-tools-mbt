import json
import os
import random
import string


class TextConverterException(Exception):
    """Exception when error occurs while converting the txt file to json."""


class TextConverter:

    def __init__(self, debug: bool = False):
        """
        Init method
        """
        self.reset()
        self.letters = string.ascii_letters + string.digits
        if debug:
            self.letters = "A"

    def reset(self):
        """Reset the properties values to default.
        """
        self.content = []
        self.parsed_content = []
        self.path_file = ""

    def read_content(self, path_file: str):
        """ Reads the selected file and stores the content for a posterior processing.

        Args:
            path_file: Path to the file.

        Raises:
            TextConverterException: Raised when file to be open is not found
        """

        def clean_line(line: str) -> str:
            line = line.lstrip(' ')
            i = 0
            while i < len(line):
                if line[i] not in [' ', '\t']:
                    break
                i += 1
            return line[i:len(line)]

        self.reset()
        self.path_file = path_file
        if not os.path.exists(path_file):
            raise TextConverterException(f"File: '{path_file}' not found.")
        with open(path_file, 'r') as file:
            self.content = file.readlines()
        self.content = [clean_line(x) for x in self.content]

    def process_content(self):
        """Process the current content to make it json friendly.
        """
        def has_params(line_position: int) -> bool:
            return '/' in self.content[line_position]

        def is_an_action(line_position: int) -> bool:
            actions = ['e_', 'v_', 'i_', 'iv_']
            if has_params(line_position):
                return True
            if any((self.content[line_position].startswith(x)) for x in actions):
                if '=' not in self.content[line_position]:
                    return True
            return False

        def is_empty(line: str) -> str:
            return len(line) < 2

        i = 0
        start_found = False
        # Start
        while i < len(self.content):
            if not is_empty(self.content[i]):
                if self.content[i].title().startswith("Start"):
                    start_found = True
                    i += 1
                    break
            i += 1
        if not start_found:
            raise TextConverterException(
                f"The {self.path_file} does not have 'Start' entry point format.\nCheck the example how test formats are supported")

        # steps
        state = {"e_": "v_", "i_": "iv_"}
        status = ""
        while i < len(self.content):
            if is_empty(self.content[i]):
                i += 1
                continue
            if status != "":
                if self.content[i].startswith(state[status]):
                    status = ""
                else:
                    raise TextConverterException(
                        f"Error parsing at line: {str(i + 1)} | Expected a method which starts with '{state[status]}' but received the method: {self.content[i]}")
            else:
                if self.content[i].startswith("e_") or self.content[i].startswith("i_"):
                    status = self.content[i][0:2]
                else:
                    raise TextConverterException(
                        f"Error parsing at line: {str(i + 1)} | Expected a method which starts with 'e_' or 'i_' but received the method: {self.content[i]}")
            if has_params(i):
                action = self.content[i].split('/')[0].replace(' ', '')
                params_raw = self.content[i].rstrip('\n').split('/')[1]
                params = []
                if ";" in params_raw:
                    # inline parameters,
                    params = [f"{x.lstrip(' ').rstrip(' ')};" for x in params_raw.split(';') if x != '']
                    i += 1
                else:
                    i += 1
                    while i < len(self.content):
                        if is_an_action(i):
                            break
                        params.append(self.content[i].lstrip(' ').rstrip('\n'))
                        i += 1

                if len(params) == 0:
                    raise TextConverterException(
                        f"Error parsing at line: {str(i)} | Expected a method with parameters. If not, do not use the '/' at the end of the line")
                self.parsed_content.append((action, params))
            else:
                self.parsed_content.append(
                    (self.content[i].replace('\n', '').replace(' ', ''), []))
                i += 1

        if status != "":
            raise TextConverterException(
                f"Error parsing at line: {str(i + 1)} | Expected a method which starts with '{state[status]}' but reached the end of the file (EOL)")

        if len(self.parsed_content) == 0:
            raise TextConverterException(f"Error parsing file: {self.path_file} | No methods found.")

    def convert_to_JSON(self, path_to_file: str, generator: str = "random(edge_coverage(100))"):
        """Converts the data to Json format and stores it in a file.

        Args:
            path_file: Path to the file.
            generator: The mode the graphwalker will generate the steps.
        """
        vertex_defaults = {'properties': {
            'x': 0.0, 'y': 0.0, 'description': ''}}
        edge_defaults = {'properties': {'description': ''},
                         'weight': 0.0, 'dependency': 0}

        self.read_content(path_to_file)
        self.process_content()
        general_id = ''.join(random.choice(self.letters) for _ in range(20))
        basename = os.path.splitext(os.path.basename(path_to_file))[0]
        id = ""
        vertices = []
        edges = []
        action_counter = 1
        for action, params in self.parsed_content:
            if action.startswith('e_') or action.startswith('i_'):
                edge = {}
                if action_counter != 1:
                    edge['sourceVertexId'] = f"n/{general_id}-{str(action_counter - 1)}"
                edge['name'] = action
                edge['id'] = f"e/{general_id}-{str(action_counter)}"
                edge['targetVertexId'] = f"n/{general_id}-{str(action_counter + 1)}"
                if len(params) > 0:
                    edge['actions'] = params
                edge.update(edge_defaults)
                edges.append(edge)
            elif action.startswith('v_') or action.startswith('iv_'):
                vertex = {}
                vertex['name'] = action
                vertex['id'] = f"n/{general_id}-{str(action_counter)}"
                vertex.update(vertex_defaults)
                vertices.append(vertex)
            else:
                raise TextConverterException(
                    f'Unexpected entry received: {action}')
            action_counter += 1
        data = {
            "models": [
                {
                    "name": basename,
                    "id": id,
                    "startElementId": f"e/{general_id}-1",
                    "generator": generator,
                    "vertices": vertices,
                    "edges": edges
                }
            ]
        }

        dirname = os.path.dirname(path_to_file)
        with open(f'{dirname}{os.sep}{basename}.json', 'w') as outfile:
            json.dump(data, outfile, indent=4)
