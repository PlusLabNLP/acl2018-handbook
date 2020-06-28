#!/usr/bin/env python 
# -*- coding: utf-8 -*-

"""
Generates the daily schedules for the main conference schedule. Amalgamates multiple order
files containing difference pieces of the schedule and outputs a schedule for each day,
rooted in an optionally-supplied directory.

Note: order file must be properly formatted.

Bugs: Workshop and program chairs do not like to properly format order files.

Usage: 

    cat data/{papers,shortpapers,demos,srw}/order | python order2schedule.py
"""
from __future__ import division
import re, os
import sys, csv
import argparse
from handbook import *
import math
from collections import defaultdict

PARSER = argparse.ArgumentParser(description="Generate schedules for *ACL handbooks")
PARSER.add_argument("-output_dir", dest="output_dir", default="auto/papers")
PARSER.add_argument('order_files', nargs='+', help='List of order files')
args = PARSER.parse_args()
track_name_list = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K']

if not os.path.exists(args.output_dir):
    os.makedirs(args.output_dir)

def time_min(a, b):
    ahour, amin = a.split(':')
    bhour, bmin = b.split(':')
    if ahour == bhour:
        if amin < bmin:
            return a
        elif amin > bmin:
            return b
        else:
            return a
    elif ahour < bhour:
        return a
    else:
        return b

def time_max(a, b):
    if time_min(a, b) == a:
        return b
    return a

# List of dates
dates = []
schedule = defaultdict(defaultdict)
sessions = defaultdict()
session_times = defaultdict()

for file in args.order_files:
    print file
    subconf_name = file.split('/')[1]
    for line in open(file):
        line = line.rstrip()

        print "LINE", line

        if line == '+' or line == '=':
            # this is a useless waste line
            pass
        
        elif line.startswith('*'):
            # This sets the day
            day, date, year = line[2:].split(', ')
            if not (day, date, year) in dates:
                dates.append((day, date, year))

        elif line.startswith('='):
            # This names a parallel session that runs at a certain time
            if subconf_name == 'papers' and ('Demo Session' not in line and 'Student Research Workshop' not in line):
                # ignore demo session and SRW session from main conf order file
                str = line[2:]
                time_range, session_name = str.split(' ', 1)
                sessions[session_name] = Session(line, (day, date, year))

        elif line.startswith('+'):
            if line[2:].split(' ')[0] != 'Note:':
                # This names an event that takes place at a certain time
                timerange, title = line[2:].split(' ', 1)

                if "poster" in title.lower() or "demo" in title.lower() or "best paper session" in title.lower():
                    session_name = title
                    sessions[session_name] = Session(line, (day, date, year))

        elif re.match(r'^\d+', line) is not None:
            id, rest = line.split(' ', 1)
            if re.match(r'^\d+:\d+-+\d+:\d+', rest) is not None:
                title = rest.split(' ', 1)
            else:
                title = rest

            if not sessions.has_key(session_name):
                sessions[session_name] = Session("= %s %s" % (timerange, session_name), (day, date, year))

            sessions[session_name].add_paper(Paper(line, subconf_name))

# Take all the sessions and place them at their time
for session in sorted(sessions.keys()):
    day, date, year = sessions[session].date
    timerange = sessions[session].time
#    print >> sys.stderr, "SESSION", session, day, date, year, timerange
    if not schedule[(day, date, year)].has_key(timerange):
        schedule[(day, date, year)][timerange] = []
    schedule[(day, date, year)][timerange].append(sessions[session])

def sort_times(a, b):
    ahour, amin = a[0].split('--')[0].split(':')
    bhour, bmin = b[0].split('--')[0].split(':')
    if ahour == bhour:
        return cmp(int(amin), int(bmin))
    return cmp(int(ahour), int(bhour))

def minus12(time):
    if "--" in time:
        return '--'.join(map(lambda x: minus12(x), time.split('--')))

    hours, minutes = time.split(':')
    if hours.startswith('0'):
        hours = hours[1:]
    if int(hours) >= 13:
        hours = `int(hours) - 12`

    return '%s:%s' % (hours, minutes)

# Now iterate through the combined schedule, printing, printing, printing.
# Write a file for each date. This file can then be imported and, if desired, manually edited.
print('=====================')
for date in dates:
    print(date)
    day, num, year = date
    for timerange, events in sorted(schedule[date].iteritems(), cmp=sort_times):
        start, stop = timerange.split('--')

        if not isinstance(events, list):
            continue

        parallel_sessions = filter(lambda x: isinstance(x, Session) and not x.poster, events)
        poster_sessions = filter(lambda x: isinstance(x, Session) and x.poster, events)

        # PARALLEL SESSIONS

        # Print the Session overview (single-page at-a-glance grid)
        if len(parallel_sessions) > 0:
            print(parallel_sessions[0])

            session_num = parallel_sessions[0].num

            path = os.path.join(args.output_dir, '%s-parallel-session-%s.tex' % (day, session_num))
            out = open(path, 'w')
            print >> sys.stderr, "\\input{%s}" % (path)
            
            print >>out, '\\clearpage'
            print >>out, '\\setheaders{Session %s}{\\daydateyear}' % (session_num)
            '''
            print >>out, '\\begin{SessionOverview}{Session %s}{\daydateyear}' % (session_num)
            # print the session overview
            for session in parallel_sessions:
                print >>out, '  {%s}' % (session.desc)
                # times = [minus12(p.time.split('--')[0]) for p in parallel_sessions[0].papers]
            '''

            print >>out, '\\section[Session %s Overview]{Session %s Overview -- \daydateyear}' % (session_num, session_num)
            print >>out, '\\setheaders{Session %s}{\daydateyear}' % (session_num)
            print >>out, '\\begin{center}'
            print >>out, '\\righthyphenmin2'
            print >>out, '\\sloppy'
            # print >>out, '\\begin{longtable}{p{0.8in}||p{3in}}'
            print >>out, '\\begin{longtable}{>{\RaggedRight}p{0.8in}||>{\RaggedRight}p{0.69in}|>{\RaggedRight}p{0.69in}|>{\RaggedRight}p{0.69in}|>{\RaggedRight}p{0.69in}|>{\RaggedRight}p{0.69in}}'
            for sess_i, session in enumerate(parallel_sessions):
                num_row = math.ceil(len(parallel_sessions[sess_i].papers) / 5)
                # design 2: do not use multirow
                # print >>out, '\\bf Track %s \\newline \it %s \\newline %s ' % (track_name_list[sess_i], session.desc, session.time)
                # design 2
                print >>out, '\\multirow{%d}{0.8in}{\\vspace{-2mm} \\\ \\bf Track %c \\newline \it %s \\newline %s \\hyperref[parallel-session-%s-track%c]{Abstracts}}' % (num_row, chr(sess_i + 65), session.desc, session.time, session_num, chr(sess_i + 65))
                for paper_i, paper in enumerate(parallel_sessions[sess_i].papers):
                    # design 1: list all paper
                    # print >>out, '\\papertableentry{%s}' % (paper.id)
                    # if paper_i < len(parallel_sessions[sess_i].papers) - 1:
                    #     print >>out, '\\newline'
                    # design 2: use cells
                    if paper_i % 5 != 0 or paper_i == 0:
                        print >>out, '& \\papertableentry{%s}' % (paper.id)
                    else:
                        print >>out, '\\\\ \cline{2-6}'
                        print >>out, '& \\papertableentry{%s}' % (paper.id)
                if sess_i < len(parallel_sessions) - 1:
                    print >>out, '\\\\ \hline'
            print >>out, '\\end{longtable}\end{center}'
            # print >>out, ''

            '''
            num_papers = len(parallel_sessions[0].papers)
            for paper_num in range(num_papers):
                if paper_num > 0:
                    print >>out, '  \\hline'
                # print >>out, '  \\marginnote{\\rotatebox{90}{%s}}[2mm]' % (times[paper_num])
                papers_temp = [len(session.papers) for session in parallel_sessions]
                session_temp = [session.desc for session in parallel_sessions]
                print session_temp
                print papers_temp
                print paper_num
                papers = [session.papers[paper_num] for session in parallel_sessions]
                print >>out, ' ', ' & '.join(['\\papertableentry{%s}' % (p.id) for p in papers])
                print >>out, '  \\\\'
            print >>out, '\\end{SessionOverview}\n'
            '''

            # Now print the papers in each of the sessions
            # Print the papers
            print >>out, '\\newpage'
            print >>out, '\\section{Parallel Session %s}' % (session_num)
            for i, session in enumerate(parallel_sessions):
                chair = session.chair()
                print >>out, '{\\bfseries\\large %s: %s}\\\\' % (session.name, session.desc)
                print >>out, '\\subsection{\large %s: %s}' % (session.name, session.desc)
                print >>out, '\\label{parallel-session-%s-track%c}' % (session_num, chr(i + 65))
                print >>out, '\\Track%cLoc\\hfill\\sessionchair{%s}{%s}' % (chr(i + 65),chair[0],chair[1])
                for paper in session.papers:
                    print >>out, '\\paperabstract{\\day}{%s}{}{}{%s}' % (paper.time, paper.id)
                print >>out, '\\clearpage'

            print >>out, '\n'

            out.close()

        # POSTER SESSIONS
        for session in poster_sessions:
            path = os.path.join(args.output_dir, '%s-%s.tex' % (day, session.name.replace(' ', '-')))
            out = open(path, 'w')
            print >> sys.stderr, "\\input{%s}" % (path)

            print >>out, '{\\section{%s}' % (session.name)
            print >>out, '{\\setheaders{%s}{\\daydateyear}' % (session.name)
            print >>out, '{\large Time: \emph{%s}\\hfill Location: \\PosterLoc}\\\\' % (minus12(session.time))
            chair = session.chair()
            if chair[1] != '':
                print >>out, '\\emph{\\sessionchair{%s}{%s}}' % (chair[0], chair[1])
            print >>out, '\\\\'
            for paper in session.papers:
                print >>out, '\\posterabstract{%s}' % (paper.id)
            print >>out

            out.close()
