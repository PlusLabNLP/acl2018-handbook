#!/usr/bin/env python 
# -*- coding: utf-8 -*-
# Mingyu Derek Ma, June 2020
"""
Use script to automatically:
    1) replace TACL or CL paper in order file at data/papers/order
        with TACL and CL id, so those papers can be auto retrieved metadata
        and abstract in later steps in the pipeline
        For example: change
        ! [TACL] How Furiously Can Colourless Green Ideas Sleep? Sentence Acceptability in Context %by Jey Han Lau, Carlos Santos Armendariz, Matthew Purver, Chang Shu, Shalom Lappin
        to
        1234/TACL [TACL] How Furiously Can Colourless Green Ideas Sleep? Sentence Acceptability in Context %by Jey Han Lau, Carlos Santos Armendariz, Matthew Purver, Chang Shu, Shalom Lappin
    
    2) this script will read input/tacl_papers.yaml and input/cl_papers.
        yaml as information used for the matching process

Dependencies:
    pip install pyyaml

Usage:
    python3 scripts/replace_order_file_tacl_id.py
"""

import re, os
import sys, csv
import argparse
from handbook import *
from collections import defaultdict
from pybtex.database import parse_file
import yaml
from retrieve_tacl_entries import extract_json_from_line

PARSER = argparse.ArgumentParser()
PARSER.add_argument("-yaml_tacl", default="input/tacl_papers.yaml")
PARSER.add_argument("-yaml_cl", default="input/cl_papers.yaml")
PARSER.add_argument('-order_file_path', default="data/papers/order", help='path of the order file of the main conference')
args = PARSER.parse_args()

with open(args.yaml_tacl) as f:
    tacl_entries = yaml.load(f)

with open(args.yaml_cl) as f:
    cl_entries = yaml.load(f)

list_of_lines = open(args.order_file_path, "r").readlines()
for line_num, line in enumerate(list_of_lines):
    line = line.rstrip()
    match_flag = False
    if line.startswith('!'):
        line_content = line[2:]
        if line_content.split(' ')[0] == '[TACL]':
            # TACL entries
            infojson = extract_json_from_line(line_content)
            for entry in tacl_entries:
                if infojson['author_str'] == entry['author_str'] and infojson['title_str'] == entry['title_str']:
                    # found a match entry. replace this line
                    line_new = entry['id'].split('-')[1] + '/TACL # ' + line_content + '\n'
                    list_of_lines[line_num] = line_new
                    match_flag = True
        elif line_content.split(' ')[0] == '[CL]':
            # CL entries
            infojson = extract_json_from_line(line_content)
            for entry in cl_entries:
                if infojson['author_str'] == entry['author_str'] and infojson['title_str'] == entry['title_str']:
                    # found a match entry. replace this line
                    line_new = entry['id'].split('-')[1] + '/CL # ' + line_content + '\n'
                    list_of_lines[line_num] = line_new
                    match_flag = True
        if match_flag == False and (line_content.split(' ')[0] == '[TACL]' or line_content.split(' ')[0] == '[CL]'):
            sys.stderr.write('-> No match found: \n%s\n' % line)

with open(args.order_file_path, "w") as f:
    f.writelines(list_of_lines)