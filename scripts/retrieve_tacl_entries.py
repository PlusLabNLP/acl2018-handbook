#!/usr/bin/env python 
# -*- coding: utf-8 -*-
# Mingyu Derek Ma, June 2020
"""
Use script to automatically:
    1) filter out all TACL/CL papers from `data/papers/order` file;
    2) string match to find corrensponding record in bib files of previous TACL/CL volumes;
    3) extract bib record info and save to yaml file and display left out papers for manual processing

Dependencies:
    pip install lxml
    pip install requests

Usage:
    python3 scripts/retrieve_tacl_entries.py
"""

import re, os
import sys, csv
import argparse
from handbook import *
from collections import defaultdict
from pybtex.database import parse_file
from lxml import html
import requests

PARSER = argparse.ArgumentParser()
PARSER.add_argument("-output_yaml_file_path", dest="output_dir", default="inputs/tacl_papers.yaml")
PARSER.add_argument("-tacl_bib_folder", default="bibs/TACL")
PARSER.add_argument("-cl_bib_folder", default="bibs/CL")
PARSER.add_argument('-order_file_path', default="data/papers/order", help='path of the order file of the main conference')
args = PARSER.parse_args()

tacl_entries = []
cl_entries = []

def extract_json_from_line(line_content):
    line_title_author = ' '.join(line_content.split(' ')[1:]).split(" %by ")
    infojson = {
            "title": line_title_author[0],
            "author_str": line_title_author[1]
        }
    return infojson

def look_for_match_and_save_url(bib_path, candidate_entries):
    matched_entries = []
    for filename in os.listdir(bib_path):
        print('='*20, filename)
        bib_data = parse_file(os.path.join(bib_path, filename))
        for _, entry in bib_data.entries.items():
            title_this = entry.fields['title']
            if 'url' in entry.fields:
                url_this = entry.fields['url']
            # look for possible match
            for candidate in candidate_entries:
                if candidate['title'] == title_this:
                    print("=================Match Found=================")
                    print(bib_path, filename, "\n", title_this, "\n", url_this)
                    infojson = {
                        "title": title_this,
                        "author_str": candidate['author_str'],
                        "url": url_this
                    }
                    matched_entries.append(infojson)
    return matched_entries


for line in open(args.order_file_path):
    line = line.rstrip()
    if line.startswith('!'):
        line_content = line[2:]
        if line_content.split(' ')[0] == '[TACL]':
            # TACL entries
            tacl_entries.append(extract_json_from_line(line_content))
        elif line_content.split(' ')[0] == '[CL]':
            # CL entries
            cl_entries.append(extract_json_from_line(line_content))

print('Extracted TACL Entries #: %d' % len(tacl_entries))
print('Extracted CL Entries #:   %d' % len(cl_entries))
# print(tacl_entries)
# print(cl_entries)

# read bib files and search matched Entries
# Note: seems many entries are not available at the ACL Anthology, so take bib from ACL anthology and do matching doesn't work
# matched_tacl_entries = look_for_match_and_save_url(args.tacl_bib_folder, tacl_entries)
# matched_cl_entries = look_for_match_and_save_url(args.cl_bib_folder, cl_entries)

# crawl TACL website
tacl_web_list = ['https://transacl.org/index.php/tacl/issue/view/17', 'https://transacl.org/index.php/tacl/issue/view/15', 'https://transacl.org/index.php/tacl/issue/view/14', 'https://transacl.org/index.php/tacl/issue/view/13']
tacl_web_name = ['Vol 8 (2020)', 'Vol 7 (2019)', 'Vol 6 (2018)', 'Vol 5 (2017)']
matched_tacl_entries = []
for vol_i, vol_web in enumerate(tacl_web_list):
    page = requests.get(vol_web)
    tree = html.fromstring(page.content)
    titles = tree.xpath('//td[@class="tocArticleTitleAuthors"]/div[@class="tocTitle"]/a/text()')
    authors = tree.xpath('//td[@class="tocArticleTitleAuthors"]/div[@class="tocAuthors"]/text()')
    urls = tree.xpath('//td[@class="tocArticleTitleAuthors"]/div[@class="tocTitle"]/a')
    urls = [url.get("href") for url in urls]
    authors = [authors_one.replace("\t", "") for authors_one in authors]
    authors = [authors_one.replace("\n", "") for authors_one in authors]
    authors = [authors_one.replace(",", ", ") for authors_one in authors]
    # print(titles)
    # print(urls)
    # print(authors)
    assert len(titles) == len(urls)
    assert len(titles) == len(authors)
    for title_i, title in enumerate(titles):
        for candidate_i, candidate in enumerate(tacl_entries):
            if candidate['title'] == title:
                # print("=================Match Found=================")
                # print(tacl_web_name[vol_i], "\n", title, "\n", urls[title_i])
                tacl_entries[candidate_i]['found_match'] = 1
                infojson = {
                    "title": title,
                    "author_str": authors[title_i],
                    "volume": tacl_web_name[vol_i],
                    "url": urls[title_i]
                }
                matched_tacl_entries.append(infojson)
# print(matched_tacl_entries)
print('Extracted matched TACL entries from TACL website volume TOC #: %d' % len(matched_tacl_entries))

# Show TACL articles that are not found on the website
for candidate_i, candidate in enumerate(tacl_entries):
    if 'found_match' not in candidate:
        sys.stderr.write('-> Cannot found on TACL website: \n%s\n' % candidate['title'])

# Crawl TACL website page for single article for abstract info
matched_tacl_entries_with_abstract = []
for i, article in enumerate(matched_tacl_entries):
    # print(article)
    page = requests.get(article['url'])
    tree = html.fromstring(page.content)
    title_article_page = tree.xpath('//div[@id="articleTitle"]/h3/text()')[0]
    authors_article_page = tree.xpath('//div[@id="authorString"]/em/text()')[0]
    # print(title_article_page)
    # print(authors_article_page)
    assert title_article_page == article['title']
    assert authors_article_page == article['author_str']
    try:
        abstract = tree.xpath('//div[@id="articleAbstract"]/div/p/text()')[0]
        # print(abstract)
        infojson = matched_tacl_entries[i]
        infojson['abstract'] = abstract
        matched_tacl_entries_with_abstract.append(infojson)
    except:
        sys.stderr.write('-> Cannot properly extract abstract for paper and skipped: \n%s\n' % article['title'])
        pass

print('TACL entries successfully taken abstract #: %d' % len(matched_tacl_entries_with_abstract))