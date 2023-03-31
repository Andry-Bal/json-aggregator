from collections import defaultdict
from collections.abc import Iterable, Mapping, Callable
from types import MappingProxyType
from typing import Any

# Mapping with function names as keys and callable aggregation functions as
# values. Each aggregation function should take a list of values as input.
AGG_FNS = Mapping[str, Callable[[list], Any] | None]


def identity(x):
    return x


DEFAULT_AGG_FNS: AGG_FNS = MappingProxyType({'list': identity})


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
                      agg_fns: dict[str, AGG_FNS] | None = None,
                      default_agg_fns: AGG_FNS | None = DEFAULT_AGG_FNS) -> dict[Any, dict[str, Any]]:
    """Aggregate values of multiple dictionaries by key, using provided
    aggregation functions.

    Args:
        dicts (list[dict]): List of dictionaries to be aggregated.
        agg_fns (dict[str, AGG_FNS], optional): Dictionary that maps keys of
            given `dicts` to aggregation functions for their corresponding values.
            If None, functions specified in `default_agg_fns` will be used.
            Defaults to None.
        default_agg_fns (dict[str, AGG_FNS], optional): Default aggregation
            functions to use for keys that are not present in `agg_fns`. If
            None, such keys and their corresponding values are dropped and
            will not appear in final aggregated dictionary.
            Defaults to {'list': identity}, which returns all values unchanged.

    Returns:
        dict: Aggregated dictionary.

    Examples:
        >>> dicts = [{'a': 1, 'b': 2}, {'a': 3, 'b': 4, 'c': 5}, {'c': 6}]
        >>> agg_fns = {'a': {'sum': sum, 'min': min}, 'b': {'avg': lambda x: sum(x) / len(x)}}
        >>> agg_values_by_key(dicts, agg_fns)
        {'a': {'sum': 4, 'min': 1}, 'b': {'avg': 3.0}, 'c': {'list': [5, 6]}}

        >>> dicts = [{'a': 1, 'b': 2}, {'a': 3, 'b': 4, 'c': 5}, {'c': 6}]
        >>> agg_fns = {'a': {'sum': sum, 'min': min}, 'b': {'max': max}}
        >>> agg_values_by_key(dicts, agg_fns, default_agg_fns=None)
        {'a': {'sum': 4, 'min': 1}, 'b': {'max': 4}}

        >>> dicts = [{'a': 1, 'b': 2}, {'a': 3, 'b': 4, 'c': 5}, {'c': 6}]
        >>> print(agg_values_by_key(dicts, default_agg_fns={'min':min, 'max': max})) # doctest: +NORMALIZE_WHITESPACE
        {'a': {'min': 1, 'max': 3},
        'b': {'min': 2, 'max': 4},
        'c': {'min': 5, 'max': 6}}

        >>> agg_values_by_key([{'a': 1, 'b': 2}, {'a': 3, 'b': 4}], agg_fns={'a': None})
        {'b': {'list': [2, 4]}}
    """
    if agg_fns is None and default_agg_fns is None:
        raise ValueError("Both agg_fns and default_agg_fns cannot be None at the same time.")
    agg_fns = {} if agg_fns is None else agg_fns
    out_dict = {}
    for key, values in merge_dicts(dicts).items():
        key_agg_fns = agg_fns.get(key, default_agg_fns)
        if key_agg_fns is not None:
            out_dict[key] = {agg_fn_name: agg_fn(values)
                             for agg_fn_name, agg_fn in key_agg_fns.items()}
    return out_dict
