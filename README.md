# ig-query

This README documents the usage of the `ig-query.py` script for accessing the iDefense IntelGraph Customer APIs. The script processes the rich JSON data returned by the API and optionally renders it in HTML or human-readable text format.

## Usage

The script requires an API authentication token as documented at the [IntelGraph documentation site](https://intelgraph.idefense.com/#/docs/view#page-section-2-0) (the "API code"). For security reasons, the script looks for your IG API token in the environment variable `IDEF_TOKEN` rather than specifying directly on the command line. 

The syntax is as follows:

```

None at this time.
usage: ig-query.py [-h] [--debug] [--format {html,json,markdown}] indicator
```

- `-h`: Help message
- `--format`: Specify format for output. Choices are `json`, `html`, or `markdown` (a human-readable text format).
- `--debug`: Produce additional output for debugging. This is normally not needed unless working with iDefense support.

Note that this script requires the use of the [requests](http://docs.python-requests.org/en/master/) and [Markdown](https://python-markdown.github.io/) libraries.

## Known issues

None at this time.

Please report any issues via [our GitHub page](https://github.com/iDefense/ig-query).
