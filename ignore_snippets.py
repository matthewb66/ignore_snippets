#!/usr/bin/env python

import argparse
import json

from blackduck.HubRestApi import HubInstance

def get_snippet_entries(hub, project_id, version_id, limit=1000, offset=0):
	hub._check_version_compatibility()
	paramstring = "?limit=" + str(limit) + "&offset=" + \
		str(offset) + "&filter=bomMatchType:snippet&filter=bomMatchReviewStatus:not_reviewed"
	# Using internal API - see https://jira.dc1.lan/browse/HUB-18270: Make snippet API calls for ignoring, confirming snippet matches public
	path =  "{}/internal/projects/{}/versions/{}/source-bom-entries".format(hub.get_apibase(), project_id, version_id)
	url = path + paramstring
	#print(url)
	response = hub.execute_get(url)
	jsondata = response.json()
	return jsondata

def get_ignore_snippet_json(snippet_bom_entry, ignore):
	hub._check_version_compatibility()
	for cur_fileSnippetBomComponents in snippet_bom_entry['fileSnippetBomComponents']:
		cur_fileSnippetBomComponents['ignored'] = ignore
	return [snippet_bom_entry]

def ignore_snippet_bom_entry(hub, hub_version_id, snippet_bom_entry, ignore):
	hub._check_version_compatibility()
	# Using internal API - see https://jira.dc1.lan/browse/HUB-18270: Make snippet API calls for ignoring, confirming snippet matches public
	url = "{}/v1/releases/{}/snippet-bom-entries".format(hub.get_apibase(), hub_version_id)
	body = get_ignore_snippet_json(snippet_bom_entry, ignore)
	response = hub.execute_put(url, body)
	jsondata = response.json()
	return jsondata

parser = argparse.ArgumentParser(description='Ignore (or unignore) snippets int he specified project/version using the supplied options. Running with no options apart from project and version will cause all snippets to be ignored.', prog='ignore_snippets.py')
parser.add_argument("project_name", type=str, help='Black Duck project name')
parser.add_argument("version", type=str, help='Black Duck version name')
parser.add_argument("-s", "--scoremin", type=int, default=101, help='Minimum match score percentage value (hybrid value of snippet match and likelihood that component can be copied)')
parser.add_argument("-c", "--coveragemin", type=int, default=101, help='Minimum matched lines percentage')
parser.add_argument("-z", "--sizemin", type=int, default=1000000000, help='Minimum source file size (in bytes)')
parser.add_argument("-l", "--matchedlinesmin", type=int, default=1000000, help='Minimum number of matched lines from source file')
parser.add_argument("-r", "--report", action='store_true', help='Report the snippet match values, do not ignore/unignore')
parser.add_argument("-u", "--unignore", action='store_true', help='Unignore matched snippets (undo ignore action)')

args = parser.parse_args()

hub = HubInstance()

project = hub.get_project_by_name(args.project_name)
version = hub.get_version_by_name(project, args.version)

project_id = project['_meta']['href'].split("/")[-1]
version_id = version['_meta']['href'].split("/")[-1]

if args.unignore:
	ignorestr = "Unignored"
else:
	ignorestr = "Ignored"
#print(version_id)

snippet_bom_entries = get_snippet_entries(hub, project_id, version_id)
if snippet_bom_entries:
    #print(snippet_bom_entries)
    for snippet_item in snippet_bom_entries['items']:
        blocknum = 1
        for match in snippet_item['fileSnippetBomComponents']:
            matchedlines = match['sourceEndLines'][0] - match['sourceStartLines'][0]
            if (int(match['matchScore'] * 100) < int(args.scoremin)) and (int(match['matchCoverage']) < int(args.coveragemin)) and (int(snippet_item['size']) < int(args.sizemin)) and (matchedlines < int(args.matchedlinesmin)):
                if (args.report):
                    print("File: {} (size = {})".format(snippet_item['name'], snippet_item['size']))
                    print("    Block {}: matchScore = {}%, matchCoverage = {}%, matchedLines = {} - Would be ignored".format(blocknum, int(match['matchScore'] * 100), match['matchCoverage'], matchedlines))
                else:
                    ignore_snippet_bom_entry(hub, version_id, snippet_item, not(args.unignore))
                    print("File: {} - {}".format(snippet_item['name'], ignorestr))
            elif (args.report):
                print("File: {} (size = {})".format(snippet_item['name'], snippet_item['size']))
                print("    Block {}: matchScore = {}%, matchCoverage = {}%, matchedLines = {} - Would NOT be ignored".format(blocknum, int(match['matchScore'] * 100), match['matchCoverage'], matchedlines))
  		
            blocknum += 1
