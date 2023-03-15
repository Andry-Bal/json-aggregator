import argparse
import os
import statistics as st
import sys
from collections.abc import Callable
from pathlib import Path
from types import MappingProxyType

from json_aggregator.utils import agg_values_by_key, write_json, read_matching_jsons

_aggregation_functions = MappingProxyType({
    'count': len,
    'sum': sum,
    'values': lambda vals: vals,
    'mean': st.fmean,
    'median': st.median,
    'mode': st.mode,
    'std': st.pstdev,
    'var': st.pvariance,
    'min': min,
    'max': max,
})


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
        >>>run_from_cli()

        Overriding already existing function with custom implementation and
        making changes available in command-line interface:
        >>>update_agg_fns({'mean': lambda vals: sum(vals) / len(vals)})
        >>>run_from_cli()

    Returns:
        None
    """
    global _aggregation_functions
    updated_agg_fns = dict(_aggregation_functions)
    updated_agg_fns.update(agg_fns)
    _aggregation_functions = MappingProxyType(updated_agg_fns)


def aggregate_json_values_by_key(root: str | Path,
                                 patterns: list[str],
                                 agg_fns: dict[str, Callable[[list], ...]]):
    """Aggregate values of matching JSON files by key based on the provided
    aggregation functions.

    Args:
        root (str | Path): Root directory for JSON files searching.
        patterns (list[str]): Glob patterns to match.
        agg_fns (dict[str, Callable[[list], Any]]): Dictionary with aggregation
            functions, where keys are the names of the aggregation functions,
            and values are the corresponding functions.

    Returns:
        None | dict: If any JSON files that match the provided patterns are found,
            the function returns the aggregated dictionary. If no JSON files are
            found, the function prints out an error message and returns None.
    """
    json_dicts = read_matching_jsons(root, patterns)
    if not json_dicts:
        print(f"Found no files matching {patterns} in {root}.", file=sys.stderr)
        return
    return agg_values_by_key(json_dicts, agg_fns)


def arg_parser() -> argparse.ArgumentParser:
    """Create command-line interface argument parser for this script

    Returns:
        argparse.ArgumentParser: ArgumentParser containing arguments for this
        script.
    """
    parser = argparse.ArgumentParser(usage='%(prog)s [options] root',
                                     description="Aggregate values of matching JSON files by key "
                                                 "based on the provided aggregation functions.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('root', help=" String specifying the root directory for searching")
    parser.add_argument('-p', '--patterns', nargs='+', default=['*.json'],
                        help="Relative to the `root` patterns used by glob to collect matching JSON files")
    parser.add_argument('-f', '--agg_fns', nargs='+', default=['values'], choices=_aggregation_functions.keys(),
                        help="List of aggregation functions to be applied on collected values. "
                             f"Available aggregation functions: {list(_aggregation_functions.keys())}",
                        metavar='AGG_FNS')
    parser.add_argument('-m', '--multidir', action='store_true',
                        help="Perform aggregation for each immediate subdirectory of the `root`")
    parser.add_argument('-o', '--out_fname', help="Path where aggregated JSON will be written. If `multidir` option"
                                                  "is specified, will be used relative to aggregation directory")
    return parser


def run_from_cli():
    """Execute this script with arguments provided via command line interface"""
    args = arg_parser().parse_args()
    agg_fns = {fn_name: _aggregation_functions[fn_name] for fn_name in args.agg_fns}
    write_kwargs = {'indent': 4, 'sort_keys': True}
    if args.multidir:
        subdirs = [d for d in os.scandir(args.root) if d.is_dir()]
        subdirs_aggregated = [aggregate_json_values_by_key(subdir.path, args.patterns, agg_fns) for subdir in subdirs]
        if args.out_fname:
            for subdir, aggregated in zip(subdirs, subdirs_aggregated):
                write_json(Path(subdir.path, args.out_fname), aggregated, **write_kwargs)
        else:
            print(*(f"{subdir.name}:\n\t{aggregated}" for subdir, aggregated in zip(subdirs, subdirs_aggregated)),
                  sep='\n')
    else:
        aggregated = aggregate_json_values_by_key(args.root, args.patterns, agg_fns)
        write_json(args.out_fname, aggregated, **write_kwargs) if args.out_fname else print(aggregated)


if __name__ == '__main__':
    run_from_cli()
