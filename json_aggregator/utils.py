import argparse
import json
from collections.abc import Iterable, Mapping, Generator
from pathlib import Path
from typing import Any


def all_keys(dicts: Iterable[dict]) -> set:
    """Return a set of all the keys present in the given dictionaries."""
    return {k for d in dicts for k in d.keys()}


def flatten_dict_gen(d: Mapping[str, Any],
                     parent_key: str | None = None,
                     delimiter: str = '.') -> Generator[tuple[str, Any], None, None]:
    """Generator that recursively flattens a nested dictionary.

        Args:
            d (Mapping[str, Any]): Dictionary to flatten.
            parent_key (str, optional): Parent key to prepend to flattened keys.
            delimiter (str, optional): Delimiter to use between keys.

        Yields:
            tuple[str, ...]: A tuple of (key, value) pairs for each key-value
                pair in the flattened dictionary.

        Examples:
            # Flatten a nested dictionary
            >>> d = {'a': {'b': 1, 'c': {'d': 2}}}
            >>> gen = flatten_dict_gen(d)
            >>> list(gen)
            [('a.b', 1), ('a.c.d', 2)]

            # Flatten a nested dictionary with a custom delimiter
            >>> d = {'a': {'b': 1, 'c': {'d': 2}}}
            >>> gen = flatten_dict_gen(d, delimiter='_')
            >>> list(gen)
            [('a_b', 1), ('a_c_d', 2)]

        """
    for k, v in d.items():
        new_key = parent_key + delimiter + k if parent_key is not None else k
        if isinstance(v, Mapping):
            yield from flatten_dict(v, new_key, delimiter).items()
        else:
            yield new_key, v


def flatten_dict(d: Mapping[str, Any], parent_key: str | None = None, delimiter: str = '.') -> dict[str, Any]:
    """Flatten a nested dictionary

    Uses a recursive generator. The keys in the returned dictionary are composed
    of the nested keys of the original dictionary separated by the delimiter argument.

    Args:
        d (Mapping[str, Any]): Dictionary to flatten.
        parent_key (str, optional): Parent key to prepend to flattened keys.
        delimiter (str, optional): Delimiter to use between keys.

    Returns:
        dict[str, ...]: A flattened dictionary with concatenated keys from the
            original nested dictionary.
    """
    return dict(flatten_dict_gen(d, parent_key, delimiter))


def multi_pattern_glob(path: Path | str, patterns: Iterable[str]) -> list[Path]:
    """Iterate over subtree of path and yield all existing files (of any
        kind, including directories) matching the given relative patterns.

    Args:
        path (Path | str): Path to search for matching files.
        patterns (Iterable[str]): Glob patterns to match.

    Returns:
        list[Path]: List of file paths that match any of the given patterns.
    """
    matching_files = []
    for pattern in patterns:
        matching_files.extend(Path(path).glob(pattern))
    return matching_files


def read_json(fname: str | Path, **kwargs):
    """Read the contents of a JSON file and return its deserialized
    representation as a Python object.

    Args:
        fname (str | Path): Path to the JSON file to be read.
        **kwargs: Additional keyword arguments to be passed
            to the underlying 'json.load()' function.

    Returns:
        Deserialized representation of the JSON data as a Python object.
    """
    with open(fname) as file:
        contents = json.load(file, **kwargs)
    return contents


def write_json(fname: str | Path, contents: dict, **kwargs):
    """Write a Python dictionary to a JSON file.

    Args:
        fname (str | Path): The file name or path to create or overwrite.
        contents (dict): The Python dictionary to be written in the JSON file.
        **kwargs: Additional keyword arguments to be passed to the underlying
            'json.dump()' function.

    Returns:
        None
    """
    with open(fname, 'w') as file:
        json.dump(contents, file, **kwargs)


def read_matching_jsons(root: str | Path,
                        patterns: list[str]):
    """Find and read all matching JSON files found in a directory.

     Searches for all files in the given root that match at least one of the
     provided glob patterns, and returns a list of dictionaries containing the
     contents of each matching JSON file.

     Args:
         root (str | Path): Root directory for JSON files searching.
         patterns (list[str]): Glob patterns to match.

     Returns:
         list[dict]: A list of dictionaries, where each dictionary contains the
         contents of a matching JSON file.
     """
    return [read_json(path) for path in multi_pattern_glob(root, patterns)]


class KeyValueAction(argparse.Action):
    """Custom action for argparse that parses command-line arguments in the form
    of key-value pairs and builds a dictionary.

    Attributes:
        option_strings (list): A list of command-line option strings which
            should be associated with this action.
        dest (str): The name of the attribute to store the resulting dictionary.
        key_separator (str, optional): String that separates the key and value(s)
            in each key-value pair. Default is '='.
        value_separator (str, optional): String that separates multiple values
            in a single key-value pair. Default is ','.
        key_choices (list, optional): A list of valid choices for keys.
            Default is None.
        value_choices (list, optional): A list of valid choices for values.
            Default is None.
    """

    def __init__(self, option_strings, dest,
                 key_separator: str = '=',
                 value_separator: str = ',',
                 key_choices=None,
                 value_choices=None,
                 nargs=None,
                 choices=None,
                 **kwargs):
        if choices is not None:
            raise ValueError("Parameter `choices` not allowed. "
                             "Use `key_choices` and `value_choices` instead.")
        if nargs is not None:
            raise argparse.ArgumentError(self, "Parameter `nargs` not allowed.")
        self.key_separator = key_separator
        self.value_separator = value_separator
        self.key_choices = key_choices
        self.value_choices = value_choices
        super().__init__(option_strings, dest, nargs=nargs, choices=choices, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        items = getattr(namespace, self.dest, None)
        if items is None:
            items = {}
        if self.key_separator in values:
            key, vals = values.split(self.key_separator, 1)
            if self.key_choices is not None:
                self._validate_key(key)
            vals = vals.split(self.value_separator)
            if self.value_choices is not None:
                self._validate_values(vals)
            value = vals[0] if len(vals) == 1 else vals
            items[key] = value
        else:
            key = values
            if self.key_choices is not None:
                self._validate_key(key)
            items[key] = None
        setattr(namespace, self.dest, items)

    def _validate_key(self, key):
        if key not in self.key_choices:
            msg = f"invalid key choice: '{key}' " \
                  f"(chose from {', '.join(map(repr, self.key_choices))})."
            raise argparse.ArgumentError(self, msg)

    def _validate_values(self, values):
        invalid_values = set(values) - set(self.value_choices)
        if invalid_values:
            msg = f"invalid value choice(s): {', '.join(map(repr, invalid_values))} " \
                  f"(chose from {', '.join(map(repr, self.value_choices))})."
            raise argparse.ArgumentError(self, msg)
