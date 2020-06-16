# !/usr/bin/env python
# Need manual verification

import sys

author_str = sys.argv[1]

author_str = author_str.replace(' and ', ',')
author_list = author_str.split(',')
author_list = [name.strip() for name in author_list]
author_list = [' '.join(name.split(' ')[1:])+', '+name.split(' ')[0] for name in author_list]
converted_bib_author = ' and '.join(author_list)

print(converted_bib_author)