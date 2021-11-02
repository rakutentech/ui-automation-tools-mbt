import asyncio
import pypeln as pl


def flatten(d):
    """
    This flattens a nested dictionary.

    Args:
        d (dict|list): The object to flatten.

    Returns:
        flat_d (dict): The flattened object.
    """
    def recurse(value, parent_key=""):
        if isinstance(value, list):
            for i in range(len(value)):
                recurse(value[i], f'{parent_key}.{str(i)}' if parent_key else str(i))
        elif isinstance(value, dict):
            for k, v in value.items():
                recurse(v, f'{parent_key}.{k}' if parent_key else k)
        else:
            obj[parent_key] = value

    obj = {}
    recurse(d)
    return obj


def unflatten(d):
    """
    This unflattens a flattened dictionary.

    Args:
        d (dict|list): The object to flatten.

    Returns:
        items (dict): The unflattened object.
    """
    items = {}
    for k, v in d.items():
        keys = k.split('.')
        sub_items = items
        for ki in keys[:-1]:
            try:
                sub_items = sub_items[ki]
            except KeyError:
                sub_items[ki] = {}
                sub_items = sub_items[ki]
        sub_items[keys[-1]] = v
    return items


def compare_dictionaries(d1, d2, skipped_keys=None, normalize=False):
    """
    This does a general key then value mismatch comparison of two dictionaries.

    Args:
        d1 (dict): The first dictionary to compare.
        d2 (dict): The second dictionary to compare.
        skipped_keys (None|list): The keys to skip in the comparison.
        normalize (bool): Whether to convert each of the comparable values in the same casing.

    Returns:
        mismatches (dict): The record of any key and value mismatches.
    """
    flat_d1 = flatten(d1)
    flat_d2 = flatten(d2)
    skipped_keys = skipped_keys or []
    thin_keys = list(dict.fromkeys(list(flat_d1.keys()) + list(flat_d2.keys())))
    if skipped_keys:
        skipped_keys += [k for k in thin_keys if any(sk for sk in skipped_keys if sk in k)]

    mismatches = {}
    f1_not_in_f2 = [k for k in flat_d1.keys() if k not in skipped_keys and k not in flat_d2.keys()]
    f2_not_in_f1 = [k for k in flat_d2.keys() if k not in skipped_keys and k not in flat_d1.keys()]
    mismatched_keys = f1_not_in_f2 + f2_not_in_f1

    if normalize:
        mismatched_values = [{'key': k, 'd1': v, 'd2': flat_d2[k]} for k, v in flat_d1.items()
                             if k not in mismatched_keys + skipped_keys and v.lower() != flat_d2[k].lower()]
    else:
        mismatched_values = [{'key': k, 'd1': v, 'd2': flat_d2[k]} for k, v in flat_d1.items()
                             if k not in mismatched_keys + skipped_keys and v != flat_d2[k]]

    if mismatched_keys:
        keys = {'f1_not_in_f2': f1_not_in_f2, 'f2_not_in_f1': f2_not_in_f1}
        mismatches['keys'] = {k: v for k, v in keys.items() if v}
    if mismatched_values:
        mismatches['values'] = mismatched_values
    if skipped_keys:
        mismatches['skipped_keys'] = skipped_keys
    return mismatches


async def _async_compare_dictionaries(data, _return):
    """
    This async wrapper that validates downloaded image files by trying to open them.

    Args:
        data (list<dict>): The list containing each iteration-comparision to be made.
            d1 (dict): The first dictionary to compare.
            d2 (dict): The second dictionary to compare.
            skipped_keys (None|list): The keys to skip in the comparison.
            normalize (bool): Whether to convert each of the comparable values in the same casing.

    Returns:
        each : List of coroutines to execute.
    """

    def _worker(_data):
        """
        The worker/wrapper function for compare_dictionaries.

        Args:
            _data (list<dict>): The list containing each iteration-comparision to be made.
                d1 (dict): The first dictionary to compare.
                d2 (dict): The second dictionary to compare.
                skipped_keys (None|list): The keys to skip in the comparison.
                normalize (bool): Whether to convert each of the comparable values in the same casing.
        """
        mismatches = compare_dictionaries(_data['d1'], _data['d2'], skipped_keys=_data['skipped_keys'],
                                          normalize=_data['normalize'])

        if mismatches.get('keys'):
            _return['keys'] += mismatches['keys']
        if mismatches.get('values'):
            _return['values'] += mismatches['values']

    return await pl.task.each(lambda d: _worker(d), data, workers=1000)


def async_compare_dictionaries(d1, d2, skipped_keys=None, normalize=False):
    """
    This synchronous hook that asynchronous validates downloaded image files by trying to open them.

    Args:
        d1 (dict): The first dictionary to compare.
        d2 (dict): The second dictionary to compare.
        skipped_keys (None|list): The keys to skip in the comparison.
        normalize (bool): Whether to convert each of the comparable values in the same casing.

    Returns:
        _return (dict): The record of any key and value mismatches.
    """
    _return = {'skipped_keys': skipped_keys, 'keys': [], 'values': []}

    common_keys = set(d1).intersection(set(d2))
    missing_keys = set(d1).symmetric_difference(set(d2))
    missing_keys = [m for m in list(missing_keys) if m not in (skipped_keys or [])]

    data = [{'d1': {k: d1.get(k)},
             'd2': {k: d2.get(k)},
             'skipped_keys': skipped_keys,
             'normalize': normalize} for k in dict.fromkeys(common_keys)]

    each = _async_compare_dictionaries(data, _return)
    asyncio.run(each)

    if missing_keys:
        _return['keys'] = missing_keys

    if not _return.get('skipped_keys'):
        _return.pop('skipped_keys')
    if not _return.get('keys'):
        _return.pop('keys')
    if not _return.get('values'):
        _return.pop('values')

    return _return
