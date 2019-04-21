import argparse
import json
import os
import sys
import re

import markdown
import requests
import base64
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

def pull_report_images(match):
    match = match.group()
    try:
        response = requests.get("https://intelgraph.idefense.com/{}".format(match[1:-1]), stream=True, headers=g.config.headers)
    except:
        return match
    return "(data:image/png;base64,{})".format(base64.b64encode(response.content).decode("utf-8", "ignore"))

def output_markdown(data):
    md = ""
    for fundamental in data:
        if 'title' in fundamental:
            md += "# %s\n\n" % fundamental['title']
        else:
            md += "# %s\n\n" % fundamental['key']
        if 'abstract' in fundamental:
            md += "## Abstract: \n"
            md += fundamental['abstract']
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
        if 'analysis' in fundamental:
            md += "## Analysis: \n"
            md += re.sub(r'\(\/rest(.*?)\.(png|jpg|gif|jpeg)\)', pull_report_images, fundamental['analysis'])

        if 'mitigation' in fundamental:
            md += "## Mitigation: \n"
            md += fundamental['mitigation']
        md += "\n---\n\n"
    return md


def get_fundamentals(filename):
    with open(filename, 'r') as f:
        fundamentals = f.read().split('\n')

    return fundamentals


def get_intel(fundamentals, handle):
    intel = []
    for fundamental in fundamentals:
        if len(fundamental) == 0:
            continue

        try:
            r = requests.get(g.config.url + '%s?uuid.values=%s' % (handle, fundamental), headers=g.config.headers)
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
            sys.exit('Unexpected results for %s %s\n' % (handle, fundamental))

    return intel


def main():
    parser = argparse.ArgumentParser(description='Query iDefense IntelGraph for information on a particular key (fundamental)')
    parser.add_argument('uuid', nargs='?', help='Specify a UUID')
    parser.add_argument('--input', help='Specify an input file containing UUIDs')
    parser.add_argument('--type', help='Define whether to pull report or fundamental', choices=['report', 'fundamental'], default='fundamental')
    parser.add_argument('--format', help='Define output format', choices=['html', 'json', 'markdown'], default='json')
    parser.set_defaults(report=False)
    args = parser.parse_args()

    # Initial basics
    g.config.token = os.getenv('IDEF_TOKEN')
    if not g.config.token:
        sys.exit("Please provide API key in environment variable IDEF_TOKEN\n")

    g.config.headers = {"Content-Type": "application/json", "auth-token": g.config.token}

    if args.uuid:
        fundamentals = [args.uuid]
    elif args.input:
        fundamentals = get_fundamentals(args.input)
    else:
        sys.exit('Please specify a key or input file containing keys\n')

    if args.type == "report":
        intel = get_intel(fundamentals, "document/v0/intelligence_alert")
    else:
        intel = get_intel(fundamentals, "fundamental/v0")

    if args.format == 'json':
        print(json.dumps(intel, indent=2))
    elif args.format == 'markdown':
        print(output_markdown(intel))
    elif args.format == 'html':
        print(output_html(intel))


if __name__ == "__main__":
    main()
