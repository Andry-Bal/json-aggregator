import argparse
import csv
import sys
from pathlib import Path

from json_aggregator.utils import multi_pattern_glob, flatten_dict, read_json, all_keys

try:
    from natsort import natsorted

    _sorted_fn = natsorted
except ImportError:
    _sorted_fn = sorted

_LOCATION_COLUMN_NAME = 'Location'


def collect_json_to_csv(root: str | Path,
                        patterns: list[str],
                        out_fname: str = 'collected.csv',
                        delimiter: str = ',',
                        restval: str = '-'):
    """Collect contents of matching JSON files, flatten them and write to a CSV
    file.

    Args:
        root (str | Path): Root directory for JSON files searching.
        patterns (list[str]): Glob patterns to match.
        out_fname (str): Filename to write the CSV to. Defaults to 'collected.csv'.
        delimiter (str): Delimiter to use when writing the CSV. Defaults to ','.
        restval (str): Value to use for missing dictionary keys when writing the CSV.
            Defaults to '-'.
    """

    location_to_contents = {path.relative_to(root): flatten_dict(read_json(path))
                            for path in multi_pattern_glob(root, patterns)}
    if not location_to_contents:
        print(f"Found no files matching {patterns} in {root}.", file=sys.stderr)
        return
    column_names = [_LOCATION_COLUMN_NAME] + _sorted_fn(all_keys(location_to_contents.values()))
    for location, contents in location_to_contents.items():
        contents[_LOCATION_COLUMN_NAME] = location
    rows_gen = (location_to_contents[location] for location in _sorted_fn(location_to_contents))
    with open(out_fname, 'w') as output_file:
        dict_writer = csv.DictWriter(output_file, restval=restval, fieldnames=column_names, delimiter=delimiter)
        dict_writer.writeheader()
        dict_writer.writerows(rows_gen)


def arg_parser():
    """Create command-line interface argument parser for this script

    Returns:
        argparse.ArgumentParser: ArgumentParser containing arguments for this
        script.
    """
    parser = argparse.ArgumentParser(prog="Collect JSON files to CSV",
                                     description="Write contents of matching JSON files to a CSV file.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('root', help=" String specifying the root directory for searching")
    parser.add_argument('-p', '--patterns', nargs='+', default=['*.json'],
                        help="Relative to the `root` patterns used by glob to collect matching JSON files")
    parser.add_argument('-o', '--out_fname', default='collected.csv', help="Path where aggregated JSON will be written")
    parser.add_argument('-d', '--delimiter', default=',', help="A string used to separate fields")
    parser.add_argument('-r', '--restval', default='-', help="If contents of matching JSON files have non-equal keys, "
                                                             "the missing values are filled-in with this value")
    return parser


if __name__ == '__main__':
    args = arg_parser().parse_args()
    collect_json_to_csv(args.root, args.patterns, args.out_fname, args.delimiter, args.restval)
