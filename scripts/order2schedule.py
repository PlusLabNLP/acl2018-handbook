#!/usr/bin/env python 
# -*- coding: utf-8 -*-
# Updated by Mingyu Derek Ma, June 2020

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
from shutil import copyfile

PARSER = argparse.ArgumentParser(description="Generate schedules for *ACL handbooks")
# when just one timezone
# PARSER.add_argument("-output_dir", dest="output_dir", default="auto/papers")
# when multiple multizone multiple versions
PARSER.add_argument("-output_dir", dest="output_dir", default="auto/schedule")
PARSER.add_argument("-day_summary_output_dir", dest="day_summary_output_dir", default="content/days")
PARSER.add_argument("-timezone", default="UTC-7")
PARSER.add_argument("-base_handbook_tex", default="template/handbook.tex")
PARSER.add_argument('order_files', nargs='+', help='List of order files')
args = PARSER.parse_args()
track_name_list = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K']

if not os.path.exists(args.output_dir):
    os.makedirs(args.output_dir)

output_dir_timezone = os.path.join(args.output_dir, args.timezone)

print "Schedule will be saved to %s" % output_dir_timezone

if not os.path.exists(output_dir_timezone):
    os.makedirs(output_dir_timezone)

if not os.path.exists(args.day_summary_output_dir):
    os.makedirs(args.day_summary_output_dir)

day_summary_output_dir_timezone = os.path.join(args.day_summary_output_dir, args.timezone)

if not os.path.exists(day_summary_output_dir_timezone):
    os.makedirs(day_summary_output_dir_timezone)

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
order_timezone = ''

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
            match = re.search("UTC(\+|-)\d+", line)
            if match != None:
                if order_timezone == '' or order_timezone == match.group(0):
                    order_timezone = match.group(0)
                else:
                    sys.stderr.write('-> Different timezone detected in the same order file: \n%s\n' % line)
                line = re.sub(r' UTC\+\d+', '', line).rstrip()
            day, date, year = line[2:].split(', ')

        elif line.startswith('='):
            # This names a parallel session that runs at a certain time
            # if subconf_name == 'papers' and ('Demo Session' not in line and 'Student Research Workshop' not in line):
            #     # ignore demo session and SRW session from main conf order file
            str = line[2:]
            time_range, session_name = str.split(' ', 1)
            if 'Demo Session' in line:
                session_name = day + session_name
            sessions[session_name] = Session(line, (day, date, year), origin_tz=order_timezone, target_tz=args.timezone)

        elif line.startswith('+'):
            if line[2:].split(' ')[0] != 'Note:':
                # This names an event that takes place at a certain time
                timerange, title = line[2:].split(' ', 1)
                title, keys = extract_keywords(title)
                if keys.has_key('by'):
                    title = "%s (%s)" % (title.strip(), keys['by'])

                if "poster" in title.lower() or "demo" in title.lower() or "best paper session" in title.lower():
                    session_name = title
                    sessions[session_name] = Session(line, (day, date, year), origin_tz=order_timezone, target_tz=args.timezone)
                
                print timerange
                print (day, date, year)
                timerange_new, (day_new, date_new, year_new) = timezone_convert(timerange, (day, date, year), order_timezone, args.timezone)
                if not schedule[(day_new, date_new, year_new)].has_key(timerange_new):
                    schedule[(day_new, date_new, year_new)][timerange_new] = []
                schedule[(day_new, date_new, year_new)][timerange_new].append(title)
                print timerange_new
                print (day_new, date_new, year_new)

        elif re.match(r'^\d+', line) is not None:
            id, rest = line.split(' ', 1)
            if re.match(r'^\d+:\d+-+\d+:\d+', rest) is not None:
                title = rest.split(' ', 1)
            else:
                title = rest

            if not sessions.has_key(session_name):
                sessions[session_name] = Session("= %s %s" % (timerange, session_name), (day, date, year), origin_tz=order_timezone, target_tz=args.timezone)

            sessions[session_name].add_paper(Paper(line, subconf_name))

# Take all the sessions and place them at their time
for session in sorted(sessions.keys()):
    day, date, year = sessions[session].date
    timerange = sessions[session].time
    # This sets the day
    if not (day, date, year) in dates:
        dates.append((day, date, year))
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
page_list_all_dates = []
for date in dates:
    print(date)
    page_list = []
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
            session_num = parallel_sessions[0].num
            session_name = parallel_sessions[0].name

            path = os.path.join(output_dir_timezone, '%s-parallel-session-%s.tex' % (day, session_num))
            out = open(path, 'w')
            page_list.append(path)
            print >> sys.stderr, "\\input{%s}" % (path)
            
            print >>out, '\\clearpage'
            if 'demo' in session_num:
                print >>out, '\\setheaders{Demo Session %s}{\\daydateyear}' % (session_num)
            else:
                print >>out, '\\setheaders{%s}{\\daydateyear}' % (session_name)
            '''
            print >>out, '\\begin{SessionOverview}{Session %s}{\daydateyear}' % (session_num)
            # print the session overview
            for session in parallel_sessions:
                print >>out, '  {%s}' % (session.desc)
                # times = [minus12(p.time.split('--')[0]) for p in parallel_sessions[0].papers]
            '''

            print >>out, '\\section[Session %s]{Session %s Overview -- \daydateyear %s}' % (session_num, session_num, parallel_sessions[0].time)
            print >>out, '\\label{parallel-session-%s}' % (session_num)
            print >>out, '\\setheaders{Session %s}{\daydateyear}' % (session_num)
            print >>out, '\\begin{center}'
            print >>out, '\\righthyphenmin2'
            print >>out, '\\sloppy'
            # print >>out, '\\begin{longtable}{p{0.8in}||p{3in}}'
            print >>out, '\\begin{longtable}{>{\RaggedRight}p{0.8in}||>{\RaggedRight}p{0.69in}|>{\RaggedRight}p{0.69in}|>{\RaggedRight}p{0.69in}|>{\RaggedRight}p{0.69in}|>{\RaggedRight}p{0.69in}}'
            for sess_i, session in enumerate(parallel_sessions):
                num_row = math.ceil(len(parallel_sessions[sess_i].papers) / 5)
                # design 1: do not use multirow
                # print >>out, '\\bf Track %s \\newline \it %s \\newline %s ' % (track_name_list[sess_i], session.desc, session.time)
                # design 2
                if num_row > 0:
                    print >>out, '\\multirow{%d}{0.8in}{ \\vspace{-2mm} \\\ ' % (num_row)
                print >>out, '\\bf Track %c \\newline \it %s \\newline \\vspace{1mm} \\normalfont \\hyperref[parallel-session-%s-track%c]{Abstracts}' % (chr(sess_i + 65), session.desc, session_num, chr(sess_i + 65))
                if num_row > 0:
                    print >>out, '}'
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
            print >>out, '\\section*{Session %s Details}' % (session_num)
            for i, session in enumerate(parallel_sessions):
                chair = session.chair()
                print >>out, '\\subsection{\large %s: %s}' % (session.name, session.desc)
                print >>out, '\\label{parallel-session-%s-track%c}' % (session_num, chr(i + 65))
                # print >>out, '\\Track%cLoc\\hfill\\sessionchair{%s}{%s}' % (chr(i + 65),chair[0],chair[1])
                # ACL2020: There is no session chair for 2020, disabled
                print >>out, '\\Track%cLoc\\\\' % (chr(i + 65))
                for paper in session.papers:
                    print >>out, '\\paperabstract{\\day}{%s}{}{}{%s}' % (session.time, paper.id)
                print >>out, '\\clearpage'

            print >>out, '\n'

            out.close()

        # POSTER SESSIONS
        for session in poster_sessions:
            path = os.path.join(output_dir_timezone, '%s-%s.tex' % (day, session.name.replace(' ', '-')))
            out = open(path, 'w')
            page_list.append(path)
            print >> sys.stderr, "\\input{%s}" % (path)

            print >>out, '{\\section{%s}' % (session.name)
            print >>out, '\\label{poster-session-%s}' % (session.num)
            print >>out, '{\\setheaders{%s}{\\daydateyear}' % (session.name)
            print >>out, '{\large Time: \emph{%s}\\hfill Location: \\PosterLoc}\\\\' % (session.time) #(minus12(session.time))
            chair = session.chair()
            if chair[1] != '':
                print >>out, '\\emph{\\sessionchair{%s}{%s}}' % (chair[0], chair[1])
            print >>out, '\\\\'
            for paper in session.papers:
                print >>out, '\\posterabstract{%s}' % (paper.id)
            print >>out
            print >>out, '\\clearpage'

            out.close()

    page_list_all_dates.append(page_list)

max_pl_session_in_a_row = 5

for date in dates:
    day, num, year = date
    path = os.path.join(output_dir_timezone, '%s-overview.tex' % (day))
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
            # print >>out, '  %s & -- & %s &' % (minus12(start), minus12(stop))
            print >>out, '  %s & -- & %s &' % (start, stop)

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
                # print >>out, '  %s & -- & %s &' % (minus12(start), minus12(stop))
                print >>out, '  %s & -- & %s &' % (start, stop)
                try:
                    loc = event.split(' ')[0].capitalize()
                except:
                    loc = "Plenary"
                event_str = "%s" % event
                # event_str = event_str.replace("&", "\&")
                if 'Keynote 1' in event_str:
                    print >>out, '  {\\bfseries \\hyperref[keynote-1]{%s}} \\hfill \emph{\\%sLoc}' % (event_str, loc)
                elif 'Keynote 2' in event_str:
                    print >>out, '  {\\bfseries \\hyperref[keynote-2]{%s}} \\hfill \emph{\\%sLoc}' % (event_str, loc)
                else:
                    if isinstance(event, basestring):
                        print >>out, '  {\\bfseries %s} \\hfill \emph{\\%sLoc}' % (event_str, loc)
                    else:
                        print >>out, '  {\\bfseries \\hyperref[poster-session-%s]{%s}} \\hfill \emph{\\%sLoc}' % (event.num, event.name, loc)
                print >>out, '  \\\\'

    print >>out, '\\end{SingleTrackSchedule}'
    print >>out, '\\clearpage'
    out.close()

# Generate tex file for dayx.tex in content/schedule/UTC+x/
# these tex are originally the ones in content/day1/day1.tex, content/day2/day2.tex etc
print "=================generating dayx.tex"
for day_i, date in enumerate(dates):
    print(date)
    day, num, year = date

    out = open(os.path.join(day_summary_output_dir_timezone, 'day%d.tex' % (day_i + 1)), 'w')
    print >>out, '\\cleardoublepage'
    print >>out, '\\chapter{Main Conference: \daydate}'
    print >>out, '\\thispagestyle{emptyheader}'

    print >>out, '\\input{%s/%s-overview.tex}' % (output_dir_timezone, day)
    # print >>out, '\\afterpage{\\null\\newpage}'

    for pagepath in page_list_all_dates[day_i]:
        # insert special session among all parallel and poster sessions here
        if 'parallel-session-4A' in pagepath:
            # insert keynote 1 before 4A
            print >>out, '\\input{content/keynote/keynote-1}'
        elif 'parallel-session-14A' in pagepath:
            # insert keynote 2 before 14A
            print >>out, '\\input{content/keynote/keynote-2}'
        print >>out, '\\input{%s}' % pagepath
    out.close()

# Generate final file used for generation final/UTC+x/handbook.tex
print "=================generating final handbook.tex"
# copy a base tex file
final_tex_path = 'handbook_%s.tex' % args.timezone
copyfile(args.base_handbook_tex, final_tex_path)

# replace some key parameters
with open(final_tex_path, 'rt') as f:
    data = f.read()
    data = data.replace('TOREPLACE_TIMEZONE', args.timezone)

with open(final_tex_path, 'wt') as f:
    f.write(data)

out = open(final_tex_path, 'a')
# for day_i, date in enumerate([dates[0]]):
for day_i, date in enumerate(dates):
    print(date)
    day, num, year = date

    print >>out, '\\setdaydateyear{%s}{%s}{%s}' % (day, num, year)
    print >>out, '\\input{%s/day%d}' % (day_summary_output_dir_timezone, (day_i + 1))
    print >>out, '\\newpage'


print >>out, '\\end{document}'
out.close()
