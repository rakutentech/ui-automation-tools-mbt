from typing import Dict, List
import re
import os
import zlib
import base64
import numpy as np
from glob import iglob
from copy import deepcopy
from subprocess import run
from shutil import copyfile
from bs4 import BeautifulSoup
from urllib.parse import unquote
import xml.etree.ElementTree as ET
from uiautomationtools.models.text_converter import TextConverter

import uiautomationtools.helpers.directory_helpers as dh
from uiautomationtools.helpers.dictionary_helpers import flatten
from uiautomationtools.helpers.json_helpers import deserialize


class ModelConversionException(Exception):
    """Exception when error occurs while generating the steps."""


def find_drawio_xml_nodes(model_name):
    """
    This finds the nodes of a drawio turned xml file.

    Args:
        model_name (str): The drawio file to xml then parse.

    Returns:
        nodes (list<dict>): The node-attributes of the xml file
    """

    def clean_values(n):
        value = n.get('value')
        if not value:
            return n

        step_name = re.findall(r'[evi]+(?:_[a-z0-9]+)+', value) or [value]
        step_name = step_name[0]

        actions = value.replace(step_name, '')
        if '=' in actions:
            text = BeautifulSoup(actions, 'lxml').text.strip()
            actions = f'|{text[1:].strip()}'

        n['value'] = f'{step_name}{actions}'
        return n

    xml_file = f'{model_name}.xml'
    copyfile(model_name, xml_file)

    tree = ET.parse(xml_file)
    data = list(tree.getroot())[0].text
    os.remove(xml_file)

    decoded_data = base64.b64decode(data)
    xml = zlib.decompress(decoded_data, -15)
    xml = unquote(xml.decode('utf-8'))

    bs = BeautifulSoup(xml, 'lxml')
    nodes = bs.find_all('mxcell')
    return {n.attrs['id']: clean_values(n.attrs) for n in nodes}


def generate_steps(model_name: str, new_steps: str, generator: str = 'random(edge_coverage(100))',
                   app_dir: str = None) -> List[Dict]:
    """
    This is the top level builder for making test steps.

    Args:
        model_name: The name of the model file - no extension needed.
        new_steps: Whether to recalculate the model steps.
        generator: The method used for building the steps.
        app_dir: App under test folder's name.

    Returns:
        steps: The list of step objects.
    """
    model_name = os.path.basename(model_name).split('.')[0]
    base_path = dh.get_root_dir()
    app_dir = app_dir or dh.get_src_app_dir()

    models_dir = f'{base_path}/tests/{app_dir}/models'
    model_files = [model for model in iglob(f'{models_dir}//**', recursive=True) if
                   model.endswith('.drawio') or model.endswith('.txt')]
    model_file = dh.find_reference_in_list(f'{model_name}.drawio', model_files) or dh.find_reference_in_list(
        f'{model_name}.txt', model_files)

    if model_file == 0:
        raise ModelConversionException(
            f"The file with the model_name: {model_name} is not found on the dir: {models_dir}")

    json_model_file = model_file.replace('.txt', '.json').replace('.drawio', '.json')

    steps_dir = f'{base_path}/tests/{app_dir}/steps'
    steps_files = list(iglob(f'{steps_dir}//**', recursive=True))
    steps_file = dh.find_reference_in_list(f'{model_name}.json', steps_files)
    dh.safe_mkdirs(steps_dir)
    steps_file = steps_file or f'{steps_dir}/{model_name}.json'

    if new_steps:
        if model_file.endswith('.drawio'):
            attrs = find_drawio_xml_nodes(model_file)

            vertex_defaults = {'properties': {'x': 0.0, 'y': 0.0, 'description': ''}}
            edge_defaults = {'properties': {'description': ''}, 'weight': 0.0, 'dependency': 0}

            start = None
            vertices = []
            edges = []
            for a in attrs.values():
                actions = None
                value = a.get('value')
                if value:
                    value_actions = value.split('|')
                    value = value_actions[0]
                    if value_actions[0] != value_actions[-1]:
                        actions = f'\n{value_actions[-1]}'

                if value == 'Start':
                    start = a
                elif a.get('parent') == a.get('vertex') and value and value != 'Start':
                    vertex = {'id': f'n/{a["id"]}', 'name': value}
                    vertices.append({**vertex, **vertex_defaults})
                elif a.get('parent') != a.get('vertex') and value:
                    parent = attrs[a['parent']]
                    source = parent.get('source')
                    target = parent.get('target')
                    if not target:
                        continue
                    edge = {'id': f'e/{a["id"]}', 'name': value,
                            'sourceVertexId': f"n/{source}", 'targetVertexId': f"n/{target}"}
                    if actions:
                        edge['actions'] = [actions]
                    edges.append({**edge, **edge_defaults})

            for e in edges:
                if start['id'] in e['sourceVertexId']:
                    e['id'] = f'e/{start["id"]}'
                    e.pop('sourceVertexId')

            models = [{'name': model_name, 'id': '',
                       'startElementId': f'e/{start["id"]}', 'generator': generator,
                       'vertices': vertices, 'edges': edges}]

            dh.make_json({'models': models}, json_model_file)


        else:
            text_model = TextConverter()
            text_model.convert_to_JSON(model_file)

        run(f'altwalker offline -m {json_model_file} "{generator}" -f {steps_file}', shell=True)

    return dh.load_json(steps_file)


def actions_to_dict(actions):
    """
    This converts the actions to a dictionary.

    Args:
        actions (list): The action parameters.

    Returns:
        actions (dict): The actions as a dict.
    """
    d = {}
    for t in actions[0].split(';'):
        if not t:
            continue
        k, v = t.replace('\n', '').split('=')
        d[k] = deserialize(v[1:-1].replace("\'", '"'))
    return d


def step_expander(steps: Dict, app_dir: str = None) -> Dict:
    """
    This expands nested(imported) steps.

    Args:
        steps: The condensed steps.
        app_dir: App under test folder's name.

    Returns:
        steps: The expanded (i - imports) steps.
    """
    steps = steps.copy()
    i_store = {}

    for i in range(1000):
        if i >= len(steps):
            break

        step = steps[i]
        name = step['name']
        actions = step.get('actions')
        if actions:
            if type(actions) is not dict:
                step['actions'] = actions_to_dict(actions)

        if 'i_' == name[:2]:
            i_steps = i_store.get(name)
            if i_steps:
                i_steps = deepcopy(i_steps)
            else:
                i_steps = generate_steps(f"test_{name[2:]}", True, app_dir=app_dir)
                i_store[name] = i_steps

            for s in i_steps:
                ancestors = s.get('ancestors', [])
                if name not in ancestors:
                    s['ancestors'] = ancestors + [name]
                if actions:
                    s_action = s.get('actions', {})
                    if type(s_action) is not dict:
                        s_action = actions_to_dict(s_action)
                    s['actions'] = {**s_action, **step['actions']}
            steps = steps[:i + 1] + i_steps + steps[i + 1:]
    return steps


def prune_steps(model_steps, decision_map=None):
    """
    This removes duplicate steps from modular models (i_).

    Args:
        model_steps (dict): The model steps (expansion should have already be done).
        decision_map (None|dict): The steps names as keys and the index to take in the event of repeated steps.

    Returns:
        pruned_steps (list): The model steps with repeated 'i_' steps removed.
    """
    default_map = (decision_map or {}).copy()
    default_map = {k: range(v) if type(v) is int and v > 0 else v for k, v in default_map.items()}

    e_v_model_steps = [m for m in model_steps if m['name'][:2] in ['e_', 'v_']]
    ancestors = [m.get('ancestors', [m['name']])[0] for m in e_v_model_steps]
    hist = {a: np.where(a == np.array(ancestors))[0].tolist() for a in ancestors}
    indices = {k: [i for i in range(len(v)) if abs(v[i] - v[i - 1]) > 1] + [len(v)] for k, v in hist.items()}
    indices = {k: [v[indices[k][i - 1]: indices[k][i]] for i in range(1, len(indices[k]))] or
                  [v[:indices[k][0]]] for k, v in hist.items()}
    filtered_indices = [v[default_map[k]] if k in default_map else v for k, v in indices.items()]
    filtered_indices = sorted(flatten(filtered_indices).values())
    pruned_steps = [e_v_model_steps[i] for i in filtered_indices]
    for p in pruned_steps.copy():
        if 'delete' in p['name'].lower():
            index = pruned_steps.index(p)
            pruned_steps.append(pruned_steps.pop(index))
    return pruned_steps


def prepare_steps(model_name, new_steps=False, decision_map=None):
    """
    This uses the above functions to prepare the test steps.

    Args:
        model_name (str): The name of the model file - no extension needed.
        new_steps (bool): Whether to recalculate the model steps.

    Returns:
        model_steps (list): The list of the models steps.
    """
    model_steps = generate_steps(model_name, new_steps=new_steps)
    model_steps = step_expander(model_steps)
    return prune_steps(model_steps, decision_map)
