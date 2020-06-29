#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Matt Post, June 2014

"""
Generates the daily overviews for the main conference schedule. Amalgamates multiple order
iles containing difference pieces of the schedule and outputs a schedule for each day,
rooted in an optionally-supplied directory.

Usage:

 sh run_order2schedule_overview.sh

"""
from __future__ import division
import re, os
import sys, csv
import argparse
from handbook import *
import math
from collections import defaultdict

PARSER = argparse.ArgumentParser(description="Generate overview schedules for *ACL handbooks")
PARSER.add_argument("-output_dir", dest="output_dir", default="auto/papers")
PARSER.add_argument('order_files', nargs='+', help='List of order files')
args = PARSER.parse_args()

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

        # print "LINE", line

        if line == '+' or line == '=':
            # this is a useless waste line
            pass
        
        elif line.startswith('*'):
            if 'UTC' in line:
                line = re.sub(r' UTC\+\d+', '', line).rstrip()
            day, date, year = line[2:].split(', ')
            if not (day, date, year) in dates:
                dates.append((day, date, year))

        elif line.startswith('='):
            if subconf_name == 'papers' and ('Demo Session' not in line and 'Student Research Workshop' not in line):
                # ignore demo session and SRW session from main conf order file
                str = line[2:]
                time_range, session_name = str.split(' ', 1)
                sessions[session_name] = Session(line, (day, date, year))

        elif line.startswith('+'):# or line.startswith('!'):
            if line[2:].split(' ')[0] != 'Note:':
                timerange, title = line[2:].split(' ', 1)
                title, keys = extract_keywords(title)
                if keys.has_key('by'):
                    title = "%s (%s)" % (title.strip(), keys['by'])
                session_name = None

                if not schedule[(day, date, year)].has_key(timerange):
                    schedule[(day, date, year)][timerange] = []
                schedule[(day, date, year)][timerange].append(title)

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
    hours, minutes = time.split(':')
    if hours.startswith('0'):
        hours = hours[1:]
    if int(hours) >= 13:
        hours = `int(hours) - 12`

    return '%s:%s' % (hours, minutes)

print dates
max_pl_session_in_a_row = 5

for date in dates:
    day, num, year = date
    path = os.path.join(args.output_dir, '%s-overview.tex' % (day))
    out = open(path, 'w')
    print >> sys.stderr, "Writing file", path
    print >>out, '\\section*{Overview}'
    print >>out, '\\renewcommand{\\arraystretch}{1.2}'
    print >>out, '\\begin{SingleTrackSchedule}'
    for timerange, events in sorted(schedule[date].iteritems(), cmp=sort_times):
        start, stop = timerange.split('--')
        if len(events) >= 3 and (hasattr(events[0], "num")):
            # Parallel sessions (assume there are at least 3)
            sessions = [x for x in events]

            # turn "Session 9A" to "Session 9"
            session_num = sessions[0].num
            title = 'Session %s' % (session_num)
            num_parallel_sessions = len(sessions)
            rooms = ['\emph{\Track%cLoc}' % (chr(65+x)) for x in range(num_parallel_sessions)]
            width = 3.12 / min([max_pl_session_in_a_row, num_parallel_sessions])
            print >>out, '  %s & -- & %s &' % (minus12(start), minus12(stop))

            # Design 1: use blocks (table cells to show parallel sessions)
            # column width in inches
            '''
            print >>out, '  \\begin{tabular}{|%s|}' % ('|'.join(['p{%.2fin}' % width for x in range(min([max_pl_session_in_a_row, num_parallel_sessions]))]))
            print >>out, '    \\multicolumn{%d}{l}{{\\bfseries %s}}\\\\\\hline' % (min([max_pl_session_in_a_row, num_parallel_sessions]),title)
            if num_parallel_sessions > max_pl_session_in_a_row:
                rows_number = int(math.ceil(num_parallel_sessions/max_pl_session_in_a_row))
                for row_count in range(rows_number):
                    sessions_this_row = sessions[row_count * max_pl_session_in_a_row:min([(row_count + 1) * max_pl_session_in_a_row, num_parallel_sessions])]
                    rooms_this_row = rooms[row_count * max_pl_session_in_a_row:min([(row_count + 1) * max_pl_session_in_a_row, num_parallel_sessions])]
                    print >>out, ' & '.join([session.desc for session in sessions_this_row]), '\\\\'
                    print >>out, ' & '.join(rooms_this_row), '\\\\'
                    if rows_number != row_count:
                        print >>out, ' \\\\\hline'
            else:
                print >>out, ' & '.join([session.desc for session in sessions]), '\\\\'
                print >>out, ' & '.join(rooms), '\\\\'
            print >>out, '\\end{tabular} \\\\'
            '''

            # Design 2: use list
            print >>out, '{\\bfseries \\hyperref[parallel-session-%s]{%s}} \\newline' % (session_num, title)
            for sess_i, session in enumerate(sessions):
                print >>out, '\\hyperref[parallel-session-%s-track%c]{%s} \\hfill %s \\newline' % (session_num, chr(sess_i + 65), session.desc, rooms[sess_i])
                if sess_i == len(sessions) - 1:
                    print >>out, '\\\\'

        else:
            for event in events:
                # A regular event
                print >>out, '  %s & -- & %s &' % (minus12(start), minus12(stop))
                try:
                    loc = event.split(' ')[0].capitalize()
                except:
                    loc = "Plenary"
                event_str = "%s" % event
                # event_str = event_str.replace("&", "\&")
                print >>out, '  {\\bfseries %s} \\hfill \emph{\\%sLoc}' % (event_str, loc)
                print >>out, '  \\\\'

    print >>out, '\\end{SingleTrackSchedule}'
    out.close()

