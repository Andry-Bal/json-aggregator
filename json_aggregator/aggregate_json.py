import argparse
import os
import statistics as st
import sys
from pathlib import Path
from types import MappingProxyType

from json_aggregator.aggregation import agg_values_by_key, AGG_FNS, DEFAULT_AGG_FNS, identity
from json_aggregator.utils import write_json, read_matching_jsons, KeyValueAction

_aggregation_functions: AGG_FNS = MappingProxyType({
    'count': len,
    'sum': sum,
    'list': identity,
    'mean': st.fmean,
    'median': st.median,
    'mode': st.mode,
    'std': st.pstdev,
    'var': st.pvariance,
    'min': min,
    'max': max,
})


def agg_fns_from_names(names: list[str]) -> AGG_FNS:
    return {fn_name: _aggregation_functions[fn_name] for fn_name in names}


def update_agg_fns(agg_fns: dict):
    """Update provided aggregation functions.

    Can be used to extend/override currently available predefined aggregation
    functions.

    Args:
        agg_fns (dict): A dictionary containing the function names and their
            corresponding callable functions.

    Examples:
        Adding a new aggregation function and making it available in
        command-line interface.
        >>>update_agg_fns({'unique': set})
        >>>main(arg_parser().parse_args())

        Overriding already existing function with custom implementation and
        making changes available in command-line interface:
        >>>update_agg_fns({'mean': lambda vals: sum(vals) / len(vals)})
        >>>main(arg_parser().parse_args())

    Returns:
        None
    """
    global _aggregation_functions
    updated_agg_fns = dict(_aggregation_functions)
    updated_agg_fns.update(agg_fns)
    _aggregation_functions = MappingProxyType(updated_agg_fns)


def aggregate_json_values_by_key(root: str | Path,
                                 patterns: list[str],
                                 agg_fns: dict[str, AGG_FNS] | None = None,
                                 default_agg_fns: AGG_FNS | None = DEFAULT_AGG_FNS):
    """Aggregate values of matching JSON files by key based on the provided
    aggregation functions.

    Args:
        root (str | Path): Root directory for JSON files searching.
        patterns (list[str]): Glob patterns to match.
        agg_fns (dict[str, AGG_FNS], optional): Dictionary that maps JSON keys
            to aggregation functions for their corresponding values.
            If None, functions specified in `default_agg_fns` will be used.
            Defaults to None.
        default_agg_fns (dict[str, AGG_FNS], optional): Default aggregation
            functions to use for keys that are not present in `agg_fns`. If
            None, such keys and their corresponding values are dropped and
            will not appear in final aggregated JSON.
            Defaults to {'list': identity}, which returns all values unchanged.

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


def arg_parser() -> argparse.ArgumentParser:
    """Create command-line interface argument parser for this script

    Returns:
        argparse.ArgumentParser: ArgumentParser containing arguments for this
        script.
    """
    parser = argparse.ArgumentParser(usage='%(prog)s [options] root',
                                     description="Aggregate values of matching JSON files by key "
                                                 "based on the provided aggregation functions.",
                                     epilog="Available aggregation functions: "
                                            f"{', '.join(map(repr, _aggregation_functions.keys()))}.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('root', help=" String specifying the root directory for searching")
    parser.add_argument('-p', '--patterns', nargs='+', default=['*.json'],
                        help="Relative to the `root` patterns used by glob to collect matching JSON files")
    parser.add_argument('-a', '--agg_fns', action=KeyValueAction, value_choices=_aggregation_functions.keys(),
                        help="String representing a key-value pair, where key is a JSON key and value "
                             "is one or multiple aggregation functions for the corresponding key's values. "
                             "If not specified, the default functions from `default_agg_fns` are used.",
                        metavar='KEY=AGG_FN,... [KEY=AGG_FN,... ...]')
    parser.add_argument('-d', '--default_agg_fns', nargs='+', choices=_aggregation_functions.keys(),
                        help="Default aggregation functions to use for keys that are not present in `agg_fns`. "
                             "If not specified, such keys and their corresponding values are dropped and will "
                             "not appear in final aggregated JSON.",
                        metavar='AGG_FN')
    parser.add_argument('-m', '--multidir', action='store_true',
                        help="Perform aggregation for each immediate subdirectory of the `root`")
    parser.add_argument('-o', '--out_fname', help="Path where aggregated JSON will be written. If `multidir` option"
                                                  "is specified, will be used relative to aggregation directory")
    return parser


def main(args):
    """Execute this script with arguments provided via command line interface"""
    agg_fns = None if args.agg_fns is None else \
        {key: agg_fns_from_names(fn_names if type(fn_names) is list else [fn_names])
         for key, fn_names in args.agg_fns.items()}
    default_agg_fns = None if args.default_agg_fns is None else \
        agg_fns_from_names(args.default_agg_fns)
    agg_roots = [Path(d) for d in os.scandir(args.root) if d.is_dir()] if args.multidir else [Path(args.root)]
    agg_root_results = [aggregate_json_values_by_key(agg_root, args.patterns, agg_fns, default_agg_fns)
                        for agg_root in agg_roots]
    for agg_root, results in zip(agg_roots, agg_root_results):
        if results is not None:
            if args.out_fname:
                out_fname = (agg_root / args.out_fname) if args.multidir else args.out_fname
                write_json(out_fname, results, indent=4, sort_keys=True)
            else:
                print(f"{agg_root.name}:\n\t" if args.multidir else "", f"{results}")


if __name__ == '__main__':
    main(arg_parser().parse_args())
