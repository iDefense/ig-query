import argparse
import json
import os
import sys

import markdown
import requests


# globals
TI_REQUEST_URL = "https://api.intelgraph.idefense.com/rest/"
API_KEY = ""
HEADERS = {}


def get_ia_title(uuid):

    API_KEY = os.getenv('IDEF_TOKEN')
    HEADERS = {"Content-Type": "application/json", "auth-token": API_KEY}

    try:
        r = requests.get(TI_REQUEST_URL + 'document/v0?uuid.values=' + uuid, headers=HEADERS)
    except requests.exceptions.ConnectionError as e:
        sys.exit("Check your network connection:\n%s" % str(e))
    except requests.exceptions.HTTPError as e:
        sys.exit("Bad HTTP response:\n%s" % str(e))

    if r.json()['total_size'] == 0:
        return "Missing Intelligence Alert"
    elif r.status_code != requests.codes.ok:
        sys.exit("Bad HTTP response fetching alert:\n%s" % str(r.status_code))
    else:
        return r.json()['results'][0]['title']


def output_html(data):
    md = output_markdown(data)
    html = markdown.markdown(md)
    return html


def output_markdown(data):
    md = ""
    md += "# %s\n\n" % data['key']
    md += "## Properties\n"
    md += "- Created on: %s\n" % data['created_on']
    md += "- Modified on: %s\n" % data['last_modified']
    if 'severity' in data:
        md += "- Severity: %d\n" % data['severity']
    if 'threat_types' in data:
        md += "- Threat Types:\n"
        for ttype in data['threat_types']:
            md += "    - %s\n" % ttype
    if 'last_seen_as' in data:
        md += "- Last seen as:\n"
        for seen in data['last_seen_as']:
            md += "    - %s\n" % seen
    if 'meta_data' in data:
        md += "- Comment: %s\n" % data['meta_data']
    if 'links' in data:
        md += "\n## Relationships\n"
        for each in data['links']:
            if each['type'] == 'intelligence_alert':
                title = get_ia_title(each['uuid'])
                md += '- Intelligence Alert: [%s](%s%s)' % (title, 'https://intelgraph.idefense.com/#/node/intelligence_alert/view/', each['uuid'])
            else:
                md += "- %s (%s): %s\n" % (each['key'], each['type'], each['relationship'])
    return md


def main():
    parser = argparse.ArgumentParser(description='Query iDefense IntelGraph for information on a particular key')
    parser.add_argument('indicator', help='Specify a key')
    parser.add_argument('--debug', action='store_true', help='Print additional debug output')
    parser.add_argument('--format', help='Define output format', choices=['html', 'json', 'markdown'], default='json')
    args = parser.parse_args()

    # Initial basics
    API_KEY = os.getenv('IDEF_TOKEN')
    if args.debug:
        sys.stderr.write('Key: %s' % API_KEY)
    if not API_KEY:
        sys.exit("Please provide API key in environment variable IDEF_TOKEN\n")

    if not args.indicator:
        sys.exit('Please specify a key or file\n')

    HEADERS = {"Content-Type": "application/json", "auth-token": API_KEY}

    try:
        r = requests.get(TI_REQUEST_URL + 'fundamental/v0?key.values=' + args.indicator, headers=HEADERS)
    except requests.exceptions.ConnectionError as e:
        sys.exit("Check your network connection:\n%s" % str(e))
    except requests.exceptions.HTTPError as e:
        sys.exit("Bad HTTP response:\n%s" % str(e))

    if r.json()['total_size'] == 0:
        sys.exit("No results found\n")
    elif r.status_code != requests.codes.ok:
        sys.exit("Bad HTTP response:\n%s" % str(r.status_code))

    if args.format == 'json':
        print(json.dumps(r.json(), indent=2))
    elif args.format == 'markdown':
        print(output_markdown(r.json()['results'][0]))
    elif args.format == 'html':
        print(output_html(r.json()['results'][0]))


if __name__ == "__main__":
    main()
