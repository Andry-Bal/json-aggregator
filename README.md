# JSON Aggregator

JSON Aggregator provides two Python scripts for aggregating and collecting data from multiple JSON files.

## Aggregate JSON files with `aggregate_json.py`

```
usage: aggregate_json.py root [options]

Aggregate values of matching JSON files by key based on the provided
aggregation functions.

positional arguments:
  root                  String specifying the root directory for searching

options:
  -h, --help            show this help message and exit
  -p PATTERNS [PATTERNS ...], --patterns PATTERNS [PATTERNS ...]
                        Relative to the `root` patterns used by glob to
                        collect matching JSON files (default: ['*.json'])
  -a KEY=AGG_FN,... [KEY=AGG_FN,... ...], --agg_fns KEY=AGG_FN,... [KEY=AGG_FN,... ...]
                        String representing a key-value pair, where key is a
                        JSON key and value is one or multiple aggregation
                        functions for the corresponding key's values. If not
                        specified, the default functions from
                        `default_agg_fns` are used. (default: None)
  -d AGG_FN [AGG_FN ...], --default_agg_fns AGG_FN [AGG_FN ...]
                        Default aggregation functions to use for keys that are
                        not present in `agg_fns`. If not specified, such keys
                        and their corresponding values are dropped and will
                        not appear in final aggregated JSON. (default:
                        ['list'])
  -o OUT_FNAME, --out_fname OUT_FNAME
                        Path to a file where aggregated JSON will be written.
                        (default: None)

Available aggregation functions: 'count', 'sum', 'list', 'mean', 'median',
'mode', 'std', 'var', 'min', 'max', 'drop'.
```

### Custom aggregation functions

It is possible to extend/override predefined aggregation functions available in CLI.

The following example adds a new aggregation function `unique` and overrides existing `mean` with custom implementation:

```python
from json_aggregator.aggregate_json import AGG_FN_CHOICES, run_from_cli

custom_agg_fns = {'unique': set, 'mean': lambda vals: sum(vals) / len(vals)}
agg_fn_choices = dict(AGG_FN_CHOICES)
agg_fn_choices.update(custom_agg_fns)

run_from_cli(agg_fn_choices)

```



## Collect JSON files to a CSV with `collect_json_to_csv.py`

```
usage: collect_json_to_csv.py [options] root

Write contents of matching JSON files to a CSV file.

positional arguments:
  root                  String specifying the root directory for searching

options:
  -h, --help            show this help message and exit
  -p PATTERNS [PATTERNS ...], --patterns PATTERNS [PATTERNS ...]
                        Relative to the `root` patterns used by glob to
                        collect matching JSON files (default: ['*.json'])
  -o OUT_FNAME, --out_fname OUT_FNAME
                        Path where resulting CSV file will be written
                        (default: collected.csv)
  -d DELIMITER, --delimiter DELIMITER
                        A string used to separate fields (default: ,)
  -r RESTVAL, --restval RESTVAL
                        If contents of matching JSON files have non-equal
                        keys, the missing values are filled-in with this value
                        (default: -)
```
