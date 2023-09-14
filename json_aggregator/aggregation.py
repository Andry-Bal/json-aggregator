from collections.abc import Iterable, Mapping, Callable
from types import MappingProxyType
from typing import Any

# Mapping with function names as keys and callable aggregation functions as
# values. Each aggregation function should take a list of values as input.
AGG_FNS = Mapping[str, Callable[[list], Any] | None]


def identity(x):
    return x


DEFAULT_AGG_FNS: AGG_FNS = MappingProxyType({'list': identity})


def agg_values_by_key(dicts: Iterable[dict],
                      agg_fns: Mapping[str, AGG_FNS] | None = None,
                      default_agg_fns: AGG_FNS | None = DEFAULT_AGG_FNS) -> dict[Any, dict[str, Any]]:
    """Aggregate values of multiple dictionaries by key, using provided
    aggregation functions.

    Args:
        dicts (Iterable[dict]): Dictionaries to be aggregated.
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
        >>> agg_values_by_key(dicts, agg_fns) == {'a': {'sum': 4, 'min': 1},
        ...                                       'b': {'avg': 3.0},
        ...                                       'c': {'list': [5, 6]}}
        True

        >>> dicts = [{'a': 1, 'b': 2}, {'a': 3, 'b': 4, 'c': 5}, {'c': 6}]
        >>> agg_fns = {'a': {'sum': sum, 'min': min}, 'b': {'max': max}}
        >>> agg_values_by_key(dicts, agg_fns, default_agg_fns=None) == {'a': {'sum': 4, 'min': 1},
        ...                                                             'b': {'max': 4}}
        True

        >>> dicts = [{'a': 1, 'b': 2}, {'a': 3, 'b': 4, 'c': 5}, {'c': 6}]
        >>> agg_values_by_key(dicts, default_agg_fns={'min':min, 'max': max}) == {'a': {'min': 1, 'max': 3},
        ...                                                                       'b': {'min': 2, 'max': 4},
        ...                                                                       'c': {'min': 5, 'max': 6}}
        True

        >>> agg_values_by_key([{'a': 1, 'b': 2}, {'a': 3, 'b': 4}], agg_fns={'a': None}) == {'b': {'list': [2, 4]}}
        True
    """
    if agg_fns is None and default_agg_fns is None:
        raise ValueError("Both agg_fns and default_agg_fns cannot be None at the same time.")
    agg_fns = {} if agg_fns is None else agg_fns
    out_dict = {}
    for key in set().union(*dicts):
        key_agg_fns = agg_fns.get(key, default_agg_fns)
        if key_agg_fns is not None:
            values_to_agg = [d[key] for d in dicts if key in d]
            out_dict[key] = {agg_fn_name: agg_fn(values_to_agg)
                             for agg_fn_name, agg_fn in key_agg_fns.items()}

    return out_dict
