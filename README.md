# JSON Aggregator

JSON Aggregator privides two Python scripts for collecting and aggregating data from multiple JSON files.

## Aggregate JSON files with `aggregate_json.py`

```
usage: aggregate_json.py [options] root

Aggregate values of matching JSON files by key based on the provided
aggregation functions.

positional arguments:
  root                  String specifying the root directory for searching

options:
  -h, --help            show this help message and exit
  -p PATTERNS [PATTERNS ...], --patterns PATTERNS [PATTERNS ...]
                        Relative to the `root` patterns used by glob to
                        collect matching JSON files (default: ['*.json'])
  -f AGG_FNS [AGG_FNS ...], --agg_fns AGG_FNS [AGG_FNS ...]
                        List of aggregation functions to be applied on
                        collected values. Available aggregation functions:
                        ['count', 'sum', 'values', 'mean', 'median', 'mode',
                        'std', 'var', 'min', 'max'] (default: ['values'])
  -m, --multidir        Perform aggregation for each immediate subdirectory of
                        the `root` (default: False)
  -o OUT_FNAME, --out_fname OUT_FNAME
                        Path where aggregated JSON will be written. If
                        `multidir` optionis specified, will be used relative
                        to aggregation directory (default: None)
```

### Custom aggregation functions

It is possible to extend/override currently available predefined aggregation functions.

The following example adds a new aggregation function `unique` and overrides existing `mean` with custom implementation:

```python
from json_aggregator.aggregate_json import run_from_cli
from json_aggregator import update_agg_fns

update_agg_fns({'unique': set, 
                'mean': lambda vals: sum(vals) / len(vals)})
run_from_cli()
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

