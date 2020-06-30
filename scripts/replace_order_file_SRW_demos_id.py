#!/usr/bin/env python 
# -*- coding: utf-8 -*-
# Mingyu Derek Ma, June 2020
"""
Use script to automatically:
    1) replace demos or SRW paper in order file at data/papers/order
        with paper id, so those papers can be auto retrieved metadata
        and abstract in later steps in the pipeline
        For example: change
        ! [SRW] Story-level Text Style Transfer: A Proposal %by Yusu Qian
        to
        17/SRW # Story-level Text Style Transfer: A Proposal %by Yusu Qian
    
    2) this script will auto/demos/papers.bib and auto/SRW/papers.bib as information used for the matching process

Dependencies:
    pip install pybtex

Usage:
    python3 scripts/replace_order_file_SRW_demos_id.py
"""

import re, os
import sys, csv
import argparse
from handbook import *
from collections import defaultdict
from pybtex.database.input import bibtex
import yaml
from retrieve_tacl_entries import extract_json_from_line

PARSER = argparse.ArgumentParser()
PARSER.add_argument("-bib_demos", default="auto/demos/papers.bib")
PARSER.add_argument("-bib_SRW", default="auto/SRW/papers.bib")
PARSER.add_argument('-order_file_path', default="data/papers/order", help='path of the order file of the main conference')
args = PARSER.parse_args()

parser = bibtex.Parser()
bib_data_demos = parser.parse_file(args.bib_demos)
bib_data_SRW = parser.parse_file(args.bib_SRW)

# create a map between title, author and key
bib_dict_demos = []
for paper_key in bib_data_demos.entries.keys():
    info_json = {
        "id": paper_key,
        "title_str": bib_data_demos.entries[paper_key].fields['TITLE']
    }
    bib_dict_demos.append(info_json)

bib_dict_SRW = []
for paper_key in bib_data_SRW.entries.keys():
    info_json = {
        "id": paper_key,
        "title_str": bib_data_SRW.entries[paper_key].fields['TITLE']
    }
    bib_dict_SRW.append(info_json)

list_of_lines = open(args.order_file_path, "r").readlines()
for line_num, line in enumerate(list_of_lines):
    line = line.rstrip()
    match_flag = False
    if line.startswith('!'):
        line_content = line[2:]
        if line_content.split(' ')[0] == '[SRW]':
            # SRW entries
            infojson = extract_json_from_line(line_content)
            for entry in bib_dict_SRW:
                if infojson['title_str'].lower() == entry['title_str'].replace('{', '').replace('}', '').lower():
                    # found a match entry. replace this line
                    if not match_flag:
                        line_new = entry['id'].split('-')[1] + '/SRW # ' + line_content + '\n'
                        list_of_lines[line_num] = line_new
                        match_flag = True
                    else:
                        sys.stderr.write('-> More than one match found: \n%s\n' % line)

        elif line_content.split(' ')[0] == '[Demo]':
            # Demo entries
            infojson = extract_json_from_line(line_content)
            for entry in bib_dict_demos:
                if infojson['title_str'].lower() == entry['title_str'].replace('{', '').replace('}', '').lower():
                    # found a match entry. replace this line
                    if not match_flag:
                        line_new = entry['id'].split('-')[1] + '/demos # ' + line_content + '\n'
                        list_of_lines[line_num] = line_new
                        match_flag = True
                    else:
                        sys.stderr.write('-> More than one match found: \n%s\n' % line)
        
        if match_flag == False and (line_content.split(' ')[0] == '[SRW]' or line_content.split(' ')[0] == '[Demo]'):
            sys.stderr.write('-> No match found: \n%s\n' % line)

with open(args.order_file_path, "w") as f:
    f.writelines(list_of_lines)