import json
from collections import defaultdict
from collections.abc import Iterable
from collections.abc import Mapping, Generator
from itertools import groupby
from pathlib import Path
from typing import Callable


def all_equal(iterable: Iterable):
    """Return True if all elements are equal, False otherwise."""
    g = groupby(iterable)
    return next(g, True) and not next(g, False)


def keys_equal(dicts: Iterable[dict]):
    """Return True if all dictionaries have the same keys, False otherwise."""
    return all_equal(d.keys() for d in dicts)


def merge_dicts(dicts: Iterable[dict]) -> dict:
    """Merge multiple dictionaries into a single dictionary, with values having
    same key merged in a list.

    Args:
        dicts (Iterable[dict]) Iterable of dictionaries to be merged.

    Returns:
        dict: Merged dictionary.

    Example:
        >>> dict1 = {'a': 1, 'b': 2}
        >>> dict2 = {'a': 3, 'c': 4}
        >>> merge_dicts([dict1, dict2])
        {'a': [1, 3], 'b': [2], 'c': [4]}

        >>> dict1 = {'a': 1, 'b': 2}
        >>> dict2 = dict()
        >>> merge_dicts([dict1, dict2])
        {'a': [1], 'b': [2]}
    """
    merged = defaultdict(list)
    for d in dicts:
        for key, value in d.items():
            merged[key].append(value)
    return dict(merged)


def agg_values_by_key(dicts: list[dict],
                      agg_fns: dict[str, Callable]) -> dict[..., dict[str, ...]]:
    """Aggregate values of multiple dictionaries by key based on given
    aggregation functions.

    Args:
        dicts (list[dict]): List of dictionaries to be merged and aggregated.
        agg_fns (dict[str, Callable])): Dictionary of aggregation functions to be
            applied on the merged values, where keys are the names of the aggregation
            functions, and values are the corresponding functions.

    Returns:
        Dictionary with keys from the merged dictionaries, and values as dictionaries
        containing the results of applying each aggregation function on the values
        corresponding to the key.

    Examples:
        >>> dicts = [{'a': 1, 'b': 2, 'c': 3}, {'a': 2, 'b': 3, 'd': 4}]
        >>> agg_fns = {'sum': sum, 'max': max, 'min': min}
        >>> agg_values_by_key(dicts, agg_fns) # doctest: +NORMALIZE_WHITESPACE
        {'a': {'sum': 3, 'max': 2, 'min': 1},
        'b': {'sum': 5, 'max': 3, 'min': 2},
        'c': {'sum': 3, 'max': 3, 'min': 3},
        'd': {'sum': 4, 'max': 4, 'min': 4}}

        >>> dicts = [{'a': 1, 'b': 2, 'c': 3}, {'a': 2, 'b': 3, 'c': 4}]
        >>> agg_fns = {'avg': lambda x: sum(x) / len(x)}
        >>> agg_values_by_key(dicts, agg_fns) # doctest: +NORMALIZE_WHITESPACE
        {'a': {'avg': 1.5},
        'b': {'avg': 2.5},
        'c': {'avg': 3.5}}

        >>> dicts = [{'a': 1, 'b': 2, 'c': 3}]
        >>> agg_fns = {'sum': sum}
        >>> agg_values_by_key(dicts, agg_fns) # doctest: +NORMALIZE_WHITESPACE
        {'a': {'sum': 1},
        'b': {'sum': 2},
        'c': {'sum': 3}}
         """
    return {key: {fn_name: agg_fn(values) for fn_name, agg_fn in agg_fns.items()}
            for key, values in merge_dicts(dicts).items()}


def all_keys(dicts: Iterable[dict]) -> set:
    """Return a set of all the keys present in the given dictionaries."""
    return {k for d in dicts for k in d.keys()}


def flatten_dict_gen(d: Mapping[str, ...],
                     parent_key: str | None = None,
                     delimiter: str = '.') -> Generator[tuple[str, ...], None, None]:
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


def flatten_dict(d: Mapping[str, ...], parent_key: str | None = None, delimiter: str = '.') -> dict[str, ...]:
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
