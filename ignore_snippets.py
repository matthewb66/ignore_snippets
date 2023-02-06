from blackduck import Client

import argparse
import logging


def get_snippet_entries(project_id, version_id):
    param_string = "?filter=bomMatchType:snippet&filter=bomMatchReviewStatus:not_reviewed"
    # Using internal API - see https://jira.dc1.lan/browse/HUB-18270: Make snippet API calls for ignoring,
    # confirming snippet matches public
    path = f"{bd.base_url}/api/internal/projects/{project_id}/versions/{version_id}/source-bom-entries"
    url = path + param_string
    #    print(url)
    snippet_entries = bd.get_items(url)
    return snippet_entries


def send_bulk_update_request(project_id, version_id, snippet_updates):
    # Using internal API - see https://jira.dc1.lan/browse/HUB-18270: Make snippet API calls for ignoring,
    # confirming snippet matches public
    url = f"/api/projects/{project_id}/versions/{version_id}/bulk-snippet-bom-entries"
    headers = {'Content-type': 'application/vnd.blackducksoftware.bill-of-materials-6+json'}
    response = bd.session.put(url, json=snippet_updates, headers=headers)
    return response


def create_snippet_update_body(snippet_bom_entry, match, ignore):
    return {
        "scanSummary": f"{bd.base_url}/api/scan-summaries/{snippet_bom_entry['scanId']}",
        "uri": snippet_bom_entry['uri'],
        "compositePath": {
            "path": snippet_bom_entry['compositePath']['path'],
            "archiveContext": snippet_bom_entry['compositePath']['archiveContext'],
            "fileName": snippet_bom_entry['compositePath']['fileName'],
            "compositePathContext": snippet_bom_entry['compositePath']['compositePathContext']
        },
        "snippetBomComponentRequests": [{
            "sourceStartLines": match['matchStartLines'],
            "sourceEndLines": match['matchEndLines'],
            "hashId": match['hashId'],
            "component": f"{bd.base_url}/api/components/{match['project']['id']}",
            "componentVersion": f"{bd.base_url}/api/components/{match['project']['id']}/versions/{match['release']['id']}",
            "origin": f"{bd.base_url}/api/components/{match['project']['id']}/versions/{match['release']['id']}/origins/{match['channelRelease']['id']}",
            "reviewStatus": match['reviewStatus'],
            "ignored": ignore
        }]
    }


logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] {%(module)s:%(lineno)d} %(levelname)s - %(message)s"
)

parser = argparse.ArgumentParser(
    description="Ignore (or unignore) snippets int he specified project/version using the supplied options. Running "
                "with no options apart from project and version will cause all snippets to be ignored.",
    prog='ignore_snippets.py')
parser.add_argument("base_url", type=str, help="Black Duck server URL e.g. https://your.blackduck.url")
parser.add_argument("token_file", type=str, help="containing access token")
parser.add_argument("project_name", type=str, help='Black Duck project name')
parser.add_argument("version_name", type=str, help='Black Duck version name')
parser.add_argument("-s", "--scoremin", type=int, default=101,
                    help='Minimum match score percentage value (hybrid value of snippet match and likelihood that '
                         'component can be copied)')
parser.add_argument("-c", "--coveragemin", type=int, default=101, help='Minimum matched lines percentage')
parser.add_argument("-z", "--sizemin", type=int, default=1000000000, help='Minimum source file size (in bytes)')
parser.add_argument("-l", "--matchedlinesmin", type=int, default=1000000,
                    help='Minimum number of matched lines from source file')
parser.add_argument("-r", "--report", action='store_true',
                    help='Report the snippet match values, do not ignore/unignore')
parser.add_argument("-u", "--unignore", action='store_true', help='Unignore matched snippets (undo ignore action)')
parser.add_argument('--no-verify', dest='verify', action='store_false', help="disable TLS certificate verification")

args = parser.parse_args()

with open(args.token_file, 'r') as tf:
    access_token = tf.readline().strip()

bd = Client(
    base_url=args.base_url,
    token=access_token,
    verify=args.verify)

params = {
    'q': [f"name:{args.project_name}"]
}
projects = [p for p in bd.get_resource('projects', params=params) if p['name'] == args.project_name]
assert len(
    projects) == 1, f"There should be one, and only one project named {args.project_name}. We found {len(projects)}"
project = projects[0]

params = {
    'q': [f"versionName:{args.version_name}"]
}
versions = [v for v in bd.get_resource('versions', project, params=params) if v['versionName'] == args.version_name]
assert len(
    versions) == 1, f"There should be one, and only one version named {args.version_name}. We found {len(versions)}"
version = versions[0]

project_id = project['_meta']['href'].split("/")[-1]
version_id = version['_meta']['href'].split("/")[-1]

if args.unignore:
    ignorestr = "Unignored"
else:
    ignorestr = "Ignored"

snippetUpdates = []
offset = 0

snippet_bom_entries = get_snippet_entries(project_id, version_id)
for snippet_item in snippet_bom_entries:
    block_num = 1
    for match in snippet_item['fileSnippetBomComponents']:
        matched_lines = match['sourceEndLines'][0] - match['sourceStartLines'][0]
        if (int(match['matchScore'] * 100) < int(args.scoremin)) and (
                int(match['matchCoverage']) < int(args.coveragemin)) and (
                int(snippet_item['size']) < int(args.sizemin)) and (matched_lines < int(args.matchedlinesmin)):
            if args.report:
                print(f"File: {snippet_item['name']} (size = {snippet_item['size']}")
                print(f"    Block {block_num}: matchScore = {int(match['matchScore'] * 100)}%, matchCoverage = {match['matchCoverage']}%, matchedLines = {matched_lines} - Would be ignored")
            else:
                snippetUpdates.append(create_snippet_update_body(snippet_item, match, not args.unignore))
                print("File: {} - {}".format(snippet_item['name'], ignorestr))
        elif args.report:
            print(f"File: {snippet_item['name']} (size = {snippet_item['size']})")
            print(f"    Block {block_num}: matchScore = {int(match['matchScore'] * 100)}%, matchCoverage = {match['matchCoverage']}%, matchedLines = {matched_lines} - Would NOT be ignored")
        if not args.report and len(snippetUpdates) >= 100:
            send_bulk_update_request(project_id, version_id, snippetUpdates)
            snippetUpdates.clear()
        block_num += 1

if not args.report and len(snippetUpdates) > 0:
    send_bulk_update_request(project_id, version_id, snippetUpdates)
