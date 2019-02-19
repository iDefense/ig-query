import argparse
import json
import os
import sys

import markdown
import requests
import globals as g


def get_ia_title(uuid):

    if __debug__:
        sys.stderr.write(f'Fetching title for {uuid}\n')

    try:
        r = requests.get(g.config.url + 'document/v0?uuid.values=' + uuid, headers=g.config.headers)
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
                if __debug__:
                    sys.stderr.write(each['uuid'] + '\n')
                title = get_ia_title(each['uuid'])
                md += '- Intelligence Alert: [%s](%s%s)' % (title, 'https://intelgraph.idefense.com/#/node/intelligence_alert/view/', each['uuid'])
            else:
                md += "- %s (%s): %s\n" % (each['key'], each['type'], each['relationship'])
    return md


def get_fundamentals(filename):
    with open(filename, 'r') as f:
        indicators = f.read().split()
    return indicators


def main():
    parser = argparse.ArgumentParser(description='Query iDefense IntelGraph for information on a particular key (fundamental)')
    parser.add_argument('key', help='Specify a key')
    parser.add_argument('--input', help='Specify an input file containing keys')
    parser.add_argument('--format', help='Define output format', choices=['html', 'json', 'markdown'], default='json')
    args = parser.parse_args()

    # Initial basics
    g.config.token = os.getenv('IDEF_TOKEN')
    if __debug__:
        sys.stderr.write('IDEF_TOKEN: %s\n' % g.config.token)
    if not g.config.token:
        sys.exit("Please provide API key in environment variable IDEF_TOKEN\n")

    g.config.headers = {"Content-Type": "application/json", "auth-token": g.config.token}

    if __debug__:
        sys.stderr.write('Key: %s\n' % args.key)
    try:
        r = requests.get(g.config.url + 'fundamental/v0?key.values=' + args.key, headers=g.config.headers)
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
        if __debug__:
            sys.stderr.write(json.dumps(r.json(), indent=2))
            sys.stderr.write('\n')
        print(output_markdown(r.json()['results'][0]))
    elif args.format == 'html':
        print(output_html(r.json()['results'][0]))


if __name__ == "__main__":

    main()
