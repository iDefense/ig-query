import argparse
import json
import os
import sys

import markdown
import requests
import globals as g


def get_ia_title(uuid):

    try:
        r = requests.get(g.config.url + 'document/v0?uuid.values=%s' % uuid, headers=g.config.headers)
    except requests.exceptions.ConnectionError as e:
        sys.exit("Check your network connection:\n%s\n" % str(e))
    except requests.exceptions.HTTPError as e:
        sys.exit("Bad HTTP response:\n%s\n" % str(e))

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
    for fundamental in data:
        md += "# %s\n\n" % fundamental['key']
        md += "## Properties\n"
        md += "- Created on: %s\n" % fundamental['created_on']
        md += "- Modified on: %s\n" % fundamental['last_modified']
        if 'severity' in fundamental:
            md += "- Severity: %d\n" % fundamental['severity']
        if 'threat_types' in fundamental:
            md += "- Threat Types:\n"
            for ttype in fundamental['threat_types']:
                md += "    - %s\n" % ttype
        if 'last_seen_as' in fundamental:
            md += "- Last seen as:\n"
            for seen in fundamental['last_seen_as']:
                md += "    - %s\n" % seen
        if 'meta_data' in fundamental:
            md += "- Comment: %s\n" % fundamental['meta_data']
        if 'links' in fundamental:
            md += "\n## Relationships\n"
            for each in fundamental['links']:
                if each['type'] == 'intelligence_alert':
                    title = get_ia_title(each['uuid'])
                    md += '- Intelligence Alert: [%s](%s%s)' % (title, 'https://intelgraph.idefense.com/#/node/intelligence_alert/view/', each['uuid'])
                else:
                    md += "- %s (%s): %s\n" % (each['key'], each['type'], each['relationship'])
        md += "\n---\n\n"
    return md


def get_fundamentals(filename):
    with open(filename, 'r') as f:
        fundamentals = f.read().split('\n')

    return fundamentals


def get_intel(fundamentals):
    intel = []
    for fundamental in fundamentals:
        if len(fundamental) == 0:
            continue

        try:
            r = requests.get(g.config.url + 'fundamental/v0?key.values=%s' % fundamental, headers=g.config.headers)
        except requests.exceptions.ConnectionError as e:
            sys.exit("Check your network connection:\n%s" % str(e))
        except requests.exceptions.HTTPError as e:
            sys.exit("Bad HTTP response:\n%s" % str(e))

        if r.status_code != requests.codes.ok:
            sys.exit("Bad HTTP response:\n%s" % str(r.status_code))
        elif r.json()['total_size'] == 0:
            sys.stderr.write('No results for %s\n' % fundamental)
        elif r.json()['total_size'] == 1:
            # We only requested one fundamental, so there SHOULD be only one result
            intel.append(r.json()['results'][0])
        else:
            sys.exit('Unexpected results for fundamental %s\n' % fundamental)

    return intel


def main():
    parser = argparse.ArgumentParser(description='Query iDefense IntelGraph for information on a particular key (fundamental)')
    parser.add_argument('key', nargs='?', help='Specify a key')
    parser.add_argument('--input', help='Specify an input file containing keys')
    parser.add_argument('--format', help='Define output format', choices=['html', 'json', 'markdown'], default='json')
    args = parser.parse_args()

    # Initial basics
    g.config.token = os.getenv('IDEF_TOKEN')
    if not g.config.token:
        sys.exit("Please provide API key in environment variable IDEF_TOKEN\n")

    g.config.headers = {"Content-Type": "application/json", "auth-token": g.config.token}

    if args.key:
        fundamentals = [args.key]
    elif args.input:
        fundamentals = get_fundamentals(args.input)
    else:
        sys.exit('Please specify a key or input file containing keys\n')

    intel = get_intel(fundamentals)

    if args.format == 'json':
        print(json.dumps(intel, indent=2))
    elif args.format == 'markdown':
        print(output_markdown(intel))
    elif args.format == 'html':
        print(output_html(intel))


if __name__ == "__main__":
    main()
