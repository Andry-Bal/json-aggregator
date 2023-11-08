import argparse
import statistics as st
import sys
from collections.abc import Iterable, Mapping, Callable
from pathlib import Path
from types import MappingProxyType
from typing import Any

from json_aggregator.utils import write_json, read_matching_jsons, KeyValueAction, identity

# Mapping with function names as keys and callable aggregation functions as
# values. Each aggregation function should take a list of values as input.
AggregationFunctions = Mapping[str, Callable[[list], Any]]
AggregationFunctionsByKey = Mapping[str, AggregationFunctions | None]

AGG_FN_CHOICES = MappingProxyType({
    'count': len,
    'sum': sum,
    'list': identity,
    'mean': st.fmean,
    'median': st.median,
    'mode': st.mode,
    'std': st.pstdev,
    'var': st.pvariance,
    'min': min,
    'max': max
})
DEFAULT_AGG_FNS: AggregationFunctions = MappingProxyType({'list': identity})

_DROP_KEYWORD = "drop"


def agg_values_by_key(dicts: Iterable[dict],
                      agg_fns: AggregationFunctionsByKey | None = None,
                      default_agg_fns: AggregationFunctions | None = DEFAULT_AGG_FNS) -> dict[Any, dict[str, Any]]:
    """Aggregate values of multiple dictionaries by key, using provided
    aggregation functions.

    Args:
        dicts (Iterable[dict]): Dictionaries to be aggregated.
        agg_fns (AggregationFunctionsByKey, optional): Dictionary that maps keys of
            given `dicts` to aggregation functions for their corresponding values.
            If key's value is None, both the key and its associated value will be
            removed and will not be included in the final aggregated dictionary.
            If None, functions specified in `default_agg_fns` will be used for all keys.
            Defaults to None.
        default_agg_fns (AggregationFunctions, optional): Default aggregation
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
        >>> agg_values_by_key(dicts, default_agg_fns={'min': min, 'max': max}) == {'a': {'min': 1, 'max': 3},
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


def agg_json_values_by_key(root: str | Path,
                           patterns: list[str],
                           agg_fns: AggregationFunctionsByKey | None = None,
                           default_agg_fns: AggregationFunctions | None = DEFAULT_AGG_FNS):
    """Aggregate values of matching JSON files by key based on the provided
    aggregation functions.

    See `agg_values_by_key`.

    Returns:
        None | dict: If any JSON files that match the provided patterns are found,
            the function returns the aggregated dictionary. If no JSON files are
            found, the function prints out an error message and returns None.
    """
    json_dicts = read_matching_jsons(root, patterns)
    if not json_dicts:
        print(f"Found no files matching {patterns} in {root}.", file=sys.stderr)
        return
    return agg_values_by_key(json_dicts, agg_fns, default_agg_fns)


def aggregate_and_output_json(root: str | Path,
                              patterns: list[str],
                              agg_fns: AggregationFunctionsByKey | None = None,
                              default_agg_fns: AggregationFunctions | None = DEFAULT_AGG_FNS,
                              out_fname: str | Path | None = None):
    aggregated = agg_json_values_by_key(root, patterns, agg_fns, default_agg_fns)
    if aggregated is not None:
        if out_fname is None:
            print(aggregated)
        else:
            write_json(out_fname, aggregated, indent=4, sort_keys=True)


def arg_parser(agg_fn_choices_names: list[str]) -> argparse.ArgumentParser:
    """Create command-line interface argument parser for this script

    Args:
        agg_fn_choices_names (list[str]): A list of available aggregation function choices' names.

    Returns:
        argparse.ArgumentParser: ArgumentParser containing arguments for this
        script.
    """
    parser = argparse.ArgumentParser(usage='%(prog)s root [options]',
                                     description="Aggregate values of matching JSON files by key "
                                                 "based on the provided aggregation functions.",
                                     epilog="Available aggregation functions: "
                                            f"{', '.join(map(repr, agg_fn_choices_names))}.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('root', help=" String specifying the root directory for searching")
    parser.add_argument('-p', '--patterns', nargs='+', default=['*.json'],
                        help="Relative to the `root` patterns used by glob to collect matching JSON files")
    parser.add_argument('-a', '--agg_fns', action=KeyValueAction, value_choices=agg_fn_choices_names,
                        help="String representing a key-value pair, where key is a JSON key and value "
                             "is one or multiple aggregation functions for the corresponding key's values. "
                             "If not specified, the default functions from `default_agg_fns` are used.",
                        metavar='KEY=AGG_FN,... [KEY=AGG_FN,... ...]')
    parser.add_argument('-d', '--default_agg_fns', nargs='+', default=['list'], choices=agg_fn_choices_names,
                        help="Default aggregation functions to use for keys that are not present in `agg_fns`. "
                             "If not specified, such keys and their corresponding values are dropped and will "
                             "not appear in final aggregated JSON.",
                        metavar='AGG_FN')
    parser.add_argument('-o', '--out_fname', help="Path to a file where aggregated JSON will be written.")
    return parser


def agg_fns_from_names(agg_fns: AggregationFunctions, names: list[str]) -> AggregationFunctions | None:
    if _DROP_KEYWORD in names:
        if len(names) != 1:
            raise ValueError(f"`{_DROP_KEYWORD}` cannot be combined with other "
                             "aggregation functions.")
        return None
    return {fn_name: agg_fns[fn_name] for fn_name in names}


def run_from_cli(agg_fn_choices: AggregationFunctions = AGG_FN_CHOICES):
    """Execute this script with arguments provided via command line interface"""
    agg_fn_choices_names = list(agg_fn_choices.keys()) + [_DROP_KEYWORD]
    args = arg_parser(agg_fn_choices_names).parse_args()
    agg_fns = None if args.agg_fns is None else \
        {key: agg_fns_from_names(agg_fn_choices, fn_names) for key, fn_names in args.agg_fns.items()}
    default_agg_fns = None if args.default_agg_fns is None else agg_fns_from_names(agg_fn_choices, args.default_agg_fns)
    aggregate_and_output_json(root=args.root,
                              patterns=args.patterns,
                              agg_fns=agg_fns,
                              default_agg_fns=default_agg_fns,
                              out_fname=args.out_fname)


def main():
    run_from_cli()


if __name__ == '__main__':
    main()
