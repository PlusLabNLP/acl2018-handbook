#!/usr/bin/env python 
# -*- coding: utf-8 -*-

"""
Takes a YAML file with TACL paper information and generates the abstract and bib files
needed to incorporate them in the handbook.

auto/tacl/papers.bib
audo/abstracts/tacl-XXX.tex
"""

import re, os
import sys, csv
import argparse
import codecs
from handbook import latex_escape
import yaml

PARSER = argparse.ArgumentParser(description="Generate schedules for *ACL handbooks")
PARSER.add_argument("-yaml_tacl", default='input/tacl_papers.yaml', type=str, help="File path for TACL YAML file")
PARSER.add_argument("-yaml_cl", default='input/cl_papers.yaml', type=str, help="File path for CL YAML file")
args = PARSER.parse_args()

for path in ['auto/tacl', 'auto/cl', 'auto/abstracts']:
    if not os.path.exists(path):
        os.makedirs(path)

def bib(paper, source_str='[TACL]'):
    str  = '@INPROCEEDINGS{%s,\n' % (paper['id'])
    str += '  AUTHOR = {%s},\n' % (paper['authors'])
    str += '  TITLE = {%s %s},\n' % (source_str, latex_escape(paper['title_str']))
    str += '  SORTNAME = {%s}}\n\n' % (paper['title_str'])
    return str

# Process TACL papers
print >> sys.stderr, "Reading from file", args.yaml_tacl
print >> sys.stderr, "Write bibtex entries to auto/tacl/papers.bib"

bibfile = codecs.open('auto/tacl/papers.bib', 'w', encoding = 'utf-8')
for paper in yaml.load(open(args.yaml_tacl)):
    bibfile.write(bib(paper, source_str='[TACL]'))

    print >> sys.stderr, "Writing abstract auto/abstracts/%s.tex" % (paper['id'])
    abstract = codecs.open('auto/abstracts/%s.tex' % (paper['id']), 'w', encoding='utf-8')
    abstract.write(latex_escape(paper['abstract']))
    abstract.close()

# Process CL papers
print >> sys.stderr, "Reading from file", args.yaml_cl
print >> sys.stderr, "Write bibtex entries to auto/cl/papers.bib"

bibfile = codecs.open('auto/cl/papers.bib', 'w', encoding = 'utf-8')
for paper in yaml.load(open(args.yaml_cl)):
    bibfile.write(bib(paper, source_str='[CL]'))

    print >> sys.stderr, "Writing abstract auto/abstracts/%s.tex" % (paper['id'])
    abstract = codecs.open('auto/abstracts/%s.tex' % (paper['id']), 'w', encoding='utf-8')
    abstract.write(latex_escape(paper['abstract']))
    abstract.close()

bibfile.close()
