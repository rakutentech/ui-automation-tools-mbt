import re


def split_all_delimiters(string):
    """
    This splits a string by all delimiters.

    Args:
        string (str): The string to split.

    Returns:
        string (str): The split string.
    """
    return re.split(r'[^a-zA-Z0-9]', string)


def delimiter_to_camelcase(string, delimiter='_', first_lower=False):
    """
    This converts a string to camelcase by delimiter.

    Args:
        string (str): The string to convert.
        delimiter (str): The delimiter of the string.
        first_lower (bool): Whether the string starts in lowercase.

    Returns:
        converted_string (str): The converted string.
    """
    if not delimiter:
        split_string = split_all_delimiters(string)
    else:
        split_string = string.split(delimiter)
    converted_string = ''.join(x.capitalize() or delimiter for x in split_string)
    if first_lower:
        converted_string = converted_string[0].lower() + converted_string[1:]
    return converted_string
