#!/usr/bin/env python 
# -*- coding: utf-8 -*-
# Mingyu Derek Ma, June 2020
"""
Use script to automatically:
    1) assign id for each discussion zoom link
    2) create a bib file containing all id to link matching

Dependencies:
    pip install pandas
    pip install xlrd

Usage:
    python3 scripts/zoomlink2bib.py
"""
import re, os
import sys, csv
import argparse
from collections import defaultdict
import json
import pandas as pd
import pprint
from collections import Counter
import yaml

PARSER = argparse.ArgumentParser()
PARSER.add_argument("-link_json", default="input/zoom_links.json")
PARSER.add_argument("-session_assignment", default="input/zoom_links_assignment.xlsx")
PARSER.add_argument("-uniq_id_prefix", default="zoom:")
PARSER.add_argument('-clean_json_path', default="auto/papers/papers_zoomlink.json", help='path of the json file for zoom link')
args = PARSER.parse_args()

# f1=open('./testfile', 'w+')
# f1.write('This is a test')
# f1.close()
# print(args, file=f1)

result = {}
with open(args.link_json, "r") as r:
    link_json = json.load(r)

df = pd.read_excel(args.session_assignment)
paper_type = []
for paper_item in link_json:
    # print (paper_item['id'])
    # line_order = int(paper_item['id'].split('.')[1])
    # print (df.iloc[line_order-1]['ID'])
    # main use xlsx to look for paper id

    paper_type.append(paper_item['content']['paper_type'])

    if paper_item['content']['paper_type'] in ['Long', 'Short']:
        # extract CL paper id from PDF url link
        line_order = int(paper_item['id'].split('.')[1])
        paper_id = "papers-" + "{0:0=3d}".format(int(df[df['Line order'] == line_order]['ID'].item()))
    elif paper_item['content']['paper_type'] == 'Demo':
        paper_id = "demos-" + "{0:0=3d}".format(int(paper_item['id'].split('.')[1]))
    elif paper_item['content']['paper_type'] == 'SRW':
        paper_id = "SRW-" + "{0:0=3d}".format(int(paper_item['id'].split('.')[1]))
    elif paper_item['content']['paper_type'] == 'CL':
        # extract CL paper id from PDF url link
        # pprint.pprint(paper_item)
        match = re.search(r"(coli|COLI)_a_(\d+)", paper_item['content']['pdf_url'])
        # paper_id = "cl-" + paper_item['content']['pdf_url'].split('/')[-1].split('_')[-1]
        paper_id = "cl-" + match.group(2)
    elif paper_item['content']['paper_type'] == 'TACL':
        paper_id = "tacl-" + "{0:0=4d}".format(int(paper_item['id'].split('.')[1]))

    for session in paper_item['content']['sessions']:
        if paper_item['content']['paper_type'] != 'Demo':
            unique_id_session_paper = '%s%s-%s' % (args.uniq_id_prefix, session['session_name'], paper_id)
        else:
            unique_id_session_paper = '%s%s-demo-%s-%s' % (args.uniq_id_prefix, session['session_name'].split('-')[1], session['session_name'].split('-')[0][1:], paper_id)
        result[unique_id_session_paper] = {
            # 'id': unique_id_session_paper,
            'title': paper_item['content']['title'],
            'zoom_link': session['zoom_link'],
            'presentation_id': paper_item['presentation_id'],
            'forum': paper_item['forum'],
            'id': paper_item['id'],
            'paper_type': paper_item['content']['paper_type'],
            'pdf_url': paper_item['content']['pdf_url']
        }


print (Counter(paper_type).keys())
print (Counter(paper_type).values())

# Save to YAML file
with open(args.clean_json_path, 'w') as file:
    json.dump(result, file)
    # yaml.dump(result, file, default_flow_style=False)