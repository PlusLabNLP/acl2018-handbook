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
import json

PARSER = argparse.ArgumentParser(description="Generate schedules for *ACL handbooks")
# when just one timezone
# PARSER.add_argument("-output_dir", dest="output_dir", default="auto/papers")
# when multiple multizone multiple versions
PARSER.add_argument("-timezone", default="UTC-7", required=True)
# Define which part of the handbook to generate
PARSER.add_argument("-sec_papers", dest="sec_papers", action='store_true',
                    help="set this flag if want to generate main conf schedules details and overviews")
PARSER.add_argument("-sec_tutorials", dest="sec_tutorials", action='store_true',
                    help="set this flag if want to generate tutorials schedules details and overviews")
PARSER.add_argument("-sec_workshops", dest="sec_workshops", action='store_true',
                    help="set this flag if want to generate tutorials schedules details and overviews")

PARSER.add_argument("-base_handbook_tex", default="template/handbook.tex")
PARSER.add_argument('-order_files', nargs='+', help='List of order files. If generate workshop schedule, the script will automatically use all folders under data/, except papers, tutorials, demos and SRW')
# For main conference
PARSER.add_argument("-output_dir", dest="output_dir", default="auto/schedule")
PARSER.add_argument("-day_summary_output_dir", dest="day_summary_output_dir", default="content/days")
PARSER.add_argument('-zoom_link_json_path', default="auto/papers/papers_zoomlink.json", help='path of the json file for zoom link')
# For tutorials
PARSER.add_argument("-output_dir_tutorials", dest="output_dir_tutorials", default="content/tutorials")
PARSER.add_argument("-base_tutorial_tex", default="content/tutorials/tutorials-overview.tex")
# For workshops
PARSER.add_argument("-output_dir_workshops", dest="output_dir_workshops", default="auto", help="it will finally become auto/workshopname/UTC+x")
PARSER.add_argument("-output_dir_workshops_tex", dest="output_dir_workshops_tex", default="content/workshops", help="it will finally become content/workshops/UTC+x")
PARSER.add_argument('-order_files_workshops', default='data/workshops/order', help='List of order files. this is the order file for all workshops overview schedule, not individual workshop order file, normally data/workshops/order')
PARSER.add_argument("-base_workshops_tex", default="content/workshops/workshops.tex")
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

if not os.path.exists(os.path.join(args.output_dir_tutorials, args.timezone)):
    os.makedirs(os.path.join(args.output_dir_tutorials, args.timezone))

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

def order2classes_workshop(order_file, target_tz):
    order_timezone = ''
    subconf_name = order_file.split('/')[1]
    schedule_list = []
    day = None
    for line_num, line in enumerate(open(order_file)):
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
                line = re.sub(r' UTC(\+|-)\d+', '', line).rstrip()
            day, date, year = line[2:].split(', ')
        elif line.startswith(('=', '+', '!')):
            str = line[2:]
            if line.startswith('='):
                level_this_line = 0
            else:
                level_this_line = 1
            # a group session containing sub items
            match_1 = re.match(r'^\d+:\d+-+\d+:\d+', str)
            match_2 = re.match(r'^\d+:\d+', str)
            if match_1 != None:
                # session time defined
                time_range, title = str.split(' ', 1)
                title, keys = extract_keywords(title)
                if keys.has_key('by'):
                    title = "%s (%s)" % (title.strip(), keys['by'])
                timerange_new, (day_new, date_new, year_new) = timezone_convert(time_range, (day, date, year), order_timezone, target_tz)
                date_new = (day_new, date_new, year_new)
            elif match_2 != None:
                time_range, title = str.split(' ', 1)
                title, keys = extract_keywords(title)
                if keys.has_key('by'):
                    title = "%s (%s)" % (title.strip(), keys['by'])
                timerange_new, (day_new, date_new, year_new) = timezone_convert(time_range, (day, date, year), order_timezone, target_tz, time_range_just_one=True)
                date_new = (day_new, date_new, year_new)
            else:
                # no session time defined
                title, keys = extract_keywords(str)
                if keys.has_key('by'):
                    title = "%s (%s)" % (title.strip(), keys['by'])
                timerange_new = None
                # if day is not None:
                #     date_new = (day, date, year)
                # else:
                date_new = None
            schedule_list.append({
                'timerange': timerange_new,
                'date': date_new,
                'title': title,
                'type': 'string_item',
                'level': level_this_line
            })
        elif re.match(r'^\d+', line) is not None:
            level_this_line = 0
            id, rest = line.split(' ', 1)
            if re.match(r'^\d+:\d+-+\d+:\d+', rest) is not None:
                title = rest.split(' ', 1)
            else:
                title = rest
            # date and timerange info will be saved in Paper entity
            # if day is not None:
            #     date_new = (day, date, year)
            # else:
            date_new = None
            _, rest = line.split(' ', 1)
            if re.match(r'^\d+:\d+', rest) is not None:
                time_range, _ = rest.split(' ', 1)
                match_1 = re.match(r'^\d+:\d+-+\d+:\d+', rest)
                flag_time_range_just_one = True
                if match_1 != None:
                    flag_time_range_just_one = False
                timerange_new, (day_new, date_new, year_new) = timezone_convert(time_range, (day, date, year), order_timezone, target_tz, time_range_just_one=flag_time_range_just_one)
                date_new = (day_new, date_new, year_new)
            else:
                timerange_new = None
                date_new = None
            schedule_list.append({
                'timerange': timerange_new,
                'date': date_new, 
                'title': title,
                'paper': Paper(line, subconf_name),
                'type': 'paper',
                'level': level_this_line
            })
    return schedule_list

def order2classes(order_files_list):
    # List of dates
    dates = []
    order_timezone = ''
    schedule = defaultdict(defaultdict)
    sessions = defaultdict()
    session_times = defaultdict()
    for file in order_files_list:
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
                    line = re.sub(r' UTC(\+|-)\d+', '', line).rstrip()
                print line
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
                    
                    timerange_new, (day_new, date_new, year_new) = timezone_convert(timerange, (day, date, year), order_timezone, args.timezone)
                    if not schedule[(day_new, date_new, year_new)].has_key(timerange_new):
                        schedule[(day_new, date_new, year_new)][timerange_new] = []
                    schedule[(day_new, date_new, year_new)][timerange_new].append(title)

            elif re.match(r'^\d+', line) is not None:
                id, rest = line.split(' ', 1)
                if re.match(r'^\d+:\d+-+\d+:\d+', rest) is not None:
                    title = rest.split(' ', 1)
                else:
                    title = rest
                try: session_name = ''
                except:
                    session_name = 'Single Paper %s' % title
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

    for sche in sorted(schedule.keys()):
        # if no parallel sessions
        if not sche in dates:
            dates.append(sche)

    return sessions, schedule, sorted(dates, key = lambda x: int(x[1].split(' ')[1]))

def gen_tex_schedule_overview(dates, schedule, target_file, mode='main-conf'):
    max_pl_session_in_a_row = 5
    if mode == 'workshops':
        out = open(target_file, 'w')
        print >> sys.stderr, "Writing file", target_file
    for date in sorted(dates, key = lambda x: int(x[1].split(' ')[1])):
        print date
        day, num, year = date
        if mode == 'main-conf':
            path = os.path.join(target_file, '%s-overview.tex' % (day))
            out = open(path, 'w')
            print >> sys.stderr, "Writing file", path
            print >>out, '\\section*{Overview}'
        else:
            print >>out, '\\section*{%s, %s}' % (day, num)
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
                    elif mode == 'main-conf':
                        if isinstance(event, basestring):
                            print >>out, '  {\\bfseries %s} \\hfill \emph{\\%sLoc}' % (event_str, loc)
                        else:
                            print >>out, '  {\\bfseries \\hyperref[poster-session-%s]{%s}} \\hfill \emph{\\%sLoc}' % (event.num, event.name, loc)
                    elif mode == 'workshops':
                        match = re.search('W(\d+):', event)
                        if match != None:
                            ws_num = int(match.group(1))
                            # print >>out, '  {\\bfseries \\hyperref[WShop%c]{%s}} \\hfill \emph{\\WShopLoc%c}' % (chr(ws_num + 64), event, chr(ws_num + 64))
                            print >>out, '  {\\bfseries \\hyperref[WShop%c]{%s}} \\hfill {\small \\href{https://virtual.acl2020.org/workshop_W%d.html}{[Web]}}' % (chr(ws_num + 64), event, ws_num)
                    print >>out, '  \\\\'

        print >>out, '\\end{SingleTrackSchedule}'
        if mode == 'main-conf':
            print >>out, '\\clearpage'
            out.close()
    if mode == 'workshops':
        print >>out, '\\clearpage'
        out.close()

def sort_times(a, b):
    ahour, amin = a[0].split('--')[0].split(':')
    ahour_e, amin_e = a[0].split('--')[1].split(':')
    bhour, bmin = b[0].split('--')[0].split(':')
    bhour_e, bmin_e = b[0].split('--')[1].split(':')
    if '+' in amin_e:
        amin_e = amin_e.split('(')[0].strip()
    if '+' in bmin_e:
        bmin_e = bmin_e.split('(')[0].strip()
    if ahour == bhour:
        if amin == bmin:
            if ahour_e == bhour_e:
                return cmp(int(amin_e), int(bmin_e))
            else:
                return cmp(int(ahour_e), int(bhour_e))
        else:
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

def gen_links_part(session_num, paper_id, zoom_dict, size="tiny", newline=False):
    zoom_link_uniq_id = 'zoom:%s-%s' % (session_num, paper_id)
    links_tex = ''
    if zoom_link_uniq_id in zoom_dict:
        zoom_link_this = zoom_dict[zoom_link_uniq_id]['zoom_link']
        presentation_id_this = zoom_dict[zoom_link_uniq_id]['presentation_id']
        pdf_url_this = zoom_dict[zoom_link_uniq_id]['pdf_url']
        if zoom_link_this != '' or pdf_url_this != '' or presentation_id_this != '':
            if newline:
                print >>out, '\\newline'
            if zoom_link_this != '':
                links_tex += '{\\%s\\href{%s}{[Zoom]}}' % (size, zoom_link_this)
            if presentation_id_this != '':
                links_tex += '{\\%s\\href{https://slideslive.com/%s}{[Talk]}}' % (size, presentation_id_this)
            if pdf_url_this != '':
                links_tex += '{\\%s\\href{%s}{[PDF]}}' % (size, pdf_url_this)
    else:
        sys.stderr.write('-> No key found: \n%s\n' % zoom_link_uniq_id)
    return links_tex

if args.sec_papers:
    sessions, schedule, dates = order2classes(args.order_files)

    # Load yaml file about Zoom Links
    with open(args.zoom_link_json_path, "r") as r:
        zoom_link_dict = json.load(r)
    # Now iterate through the combined schedule, printing, printing, printing.
    # Write a file for each date. This file can then be imported and, if desired, manually edited.
    print('=====================generating main conf schedule details')
    page_list_all_dates = []
    for date in sorted(dates, key = lambda x: int(x[1].split(' ')[1])):
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
                            links_tex = gen_links_part(session_num, paper.id, zoom_link_dict, size="tiny", newline=True)
                            print >>out, links_tex
                        else:
                            print >>out, '\\\\ \cline{2-6}'
                            print >>out, '& \\papertableentry{%s}' % (paper.id)
                            links_tex = gen_links_part(session_num, paper.id, zoom_link_dict, size="tiny", newline=True)
                            print >>out, links_tex
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
                        links_tex = gen_links_part(session_num, paper.id, zoom_link_dict, size="small")
                        print >>out, '\\paperabstract{\\day}{%s}{}{}{%s}{%s}' % (session.time, paper.id, links_tex)
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
                print >>out, '{\large Time: \emph{%s}\\hfill \\PosterLoc}\\\\' % (session.time) #(minus12(session.time))
                chair = session.chair()
                if chair[1] != '':
                    print >>out, '\\emph{\\sessionchair{%s}{%s}}' % (chair[0], chair[1])
                print >>out, '\\\\'
                for paper in session.papers:
                    links_tex = gen_links_part(session.num, paper.id, zoom_link_dict, size="small")
                    print >>out, '\\posterabstract{%s}{%s}' % (paper.id, links_tex)
                print >>out
                print >>out, '\\clearpage'

                out.close()

        page_list_all_dates.append(page_list)

    print('=====================generating main conf schedules overviews')
    gen_tex_schedule_overview(dates, schedule, output_dir_timezone, mode='main-conf')

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

if args.sec_workshops:
    sessions, schedule, dates = order2classes([args.order_files_workshops])
    print sessions
    print schedule
    print dates
    print '=================generating workshop each schedule'
    # Changed from original perl implementation in order2schedule_workshop.pl
    for ws_name in os.listdir('data'):
        # if ws_name not in ['papers', 'workshops', 'demos', 'SRW', 'tutorials', '.DS_Store']:
        if ws_name in ['WiNLP', 'iwslt', 'NLP4ConvAI', 'BioNLP2020', 'FEVER', 'iwpt', 'flp', 'nuse', 'alvr', 'RepL4NLP', 'nli', 'wngt', 'bea', 'SIGMORPHON', 'nlpmc', 'ecnlp', 'SocialNLP', 'AutoSimTrans', 'Challenge-HML']:
            print ws_name
            ws_this_schedule_list = order2classes_workshop(os.path.join('data', ws_name, 'order'), target_tz=args.timezone)
            schedule_tex_path = os.path.join(args.output_dir_workshops, ws_name, args.timezone)
            if not os.path.exists('%s/%s/%s' % (args.output_dir_workshops, ws_name, args.timezone)):
                os.makedirs('%s/%s/%s' % (args.output_dir_workshops, ws_name, args.timezone))

            out = open(os.path.join(schedule_tex_path, 'schedule.tex'), 'w')
            date_till_this_item = None
            for sche_item in ws_this_schedule_list:
                if sche_item['date'] != date_till_this_item and sche_item['date'] is not None:
                    # print new date if the event item happens in a new day
                    date_till_this_item = sche_item['date']
                    print >>out, '\\vspace{1ex}'
                    print >>out, '\\item[{\\bfseries %s, %s}]' % (date_till_this_item[0], date_till_this_item[1])
                if sche_item['level'] == 0:
                    if sche_item['type'] == 'paper':
                        if sche_item['timerange'] == None:
                            time_paper = '$\\bullet$'
                        else:
                            time_paper = sche_item['timerange']
                        print >>out, '\\item[%s] \\wspaperentry{%s}' % (time_paper, sche_item['paper'].id)
                    else:
                        # top level session containing sub items
                        print >>out, '\\vspace{1ex}'
                        if sche_item['timerange'] == None:
                            time_session = ''
                        else:
                            time_session = sche_item['timerange']
                        print >>out, '\\item[%s] {\\bfseries %s}' % (time_session, sche_item['title'])
                elif sche_item['level'] == 1:
                    # second level event
                    if sche_item['timerange'] == None:
                        time_session = ''
                    else:
                        time_session = sche_item['timerange']
                    print >>out, '\\item[%s] {%s}' % (time_session, sche_item['title'])
            out.close()

    # generate overview at content/workshop/timezone/overview.tex
    print '=================generating workshop overview'
    print dates
    overview_tex_path = os.path.join(args.output_dir_workshops_tex, args.timezone)
    if not os.path.exists(overview_tex_path):
        os.makedirs(overview_tex_path)
    overview_tex_path = os.path.join(overview_tex_path, 'overview.tex')
    gen_tex_schedule_overview(dates, schedule, overview_tex_path, mode='workshops')

    # generate overview at content/workshop/timezone/workshop.tex
    print '=================generating workshop page'
    if len(dates) <= 1:
        final_day, final_date, final_year = dates[0]
    else:
        final_day = '%s-%s' % (dates[0][0], dates[-1][0])
        final_date = '%s-%s' % (dates[0][1], dates[-1][1])
        final_year = dates[0][2]
    
    final_tex_path = '%s/%s/workshops.tex' % (args.output_dir_workshops_tex, args.timezone)
    if os.path.exists(final_tex_path):
        os.remove(final_tex_path)
    copyfile(args.base_workshops_tex, final_tex_path)
    with open(final_tex_path, 'rt') as f:
        data = f.read()
        data = data.replace('TOREPLACE_TIMEZONE', args.timezone)
        data = data.replace('TOREPLACE_WSDAY', final_day)
        data = data.replace('TOREPLACE_WSDATE', final_date)
        data = data.replace('TOREPLACE_WSYEAR', final_year)
    with open(final_tex_path, 'wt') as f:
        f.write(data)

if args.sec_tutorials:
    # GENERATE TUTORIAL OVERVIEW PAGE
    print '=================generating tutorial overview'
    final_tex_path = '%s/%s/%s' % (args.output_dir_tutorials, args.timezone, args.base_tutorial_tex.split('/')[-1])
    if os.path.exists(final_tex_path):
        os.remove(final_tex_path)
    copyfile(args.base_tutorial_tex, final_tex_path)

    # Manual input needed
    tut_time_1, tut_date_1 = timezone_convert('06:00--09:30', ("Sunday", "July 5", "2020"), 'UTC-7', args.timezone)
    tut_time_2, tut_date_2 = timezone_convert('10:30--14:00', ("Sunday", "July 5", "2020"), 'UTC-7', args.timezone)
    tut_time_3, tut_date_3 = timezone_convert('15:00--18:30', ("Sunday", "July 5", "2020"), 'UTC-7', args.timezone)

    tut_day_change_flag = False
    if tut_date_1 == tut_date_3:
        tut_final_day, tut_final_date, tut_final_year = tut_date_1
    else:
        tut_final_day = '%s-%s' % (tut_date_1[0], tut_date_3[0])
        tut_final_date = '%s-%s' % (tut_date_1[1], tut_date_3[1])
        tut_final_year = tut_date_1[2]
        tut_day_change_flag = True

    with open(final_tex_path, 'rt') as f:
        data = f.read()
        data = data.replace('TOREPLACE_TUT_TIME_A_START', tut_time_1.split('--')[0])
        data = data.replace('TOREPLACE_TUT_TIME_A_END', tut_time_1.split('--')[1])
        data = data.replace('TOREPLACE_TUT_TIME_B_START', tut_time_2.split('--')[0])
        data = data.replace('TOREPLACE_TUT_TIME_B_END', tut_time_2.split('--')[1])
        data = data.replace('TOREPLACE_TUT_TIME_C_START', tut_time_3.split('--')[0])
        data = data.replace('TOREPLACE_TUT_TIME_C_END', tut_time_3.split('--')[1])
        if tut_day_change_flag:
            # if there are more than one date for tutorial, show their separate dates there
            data = data.replace('TOREPLACE_TUT_DATE_A', "(%s, %s)" % (tut_date_1[0], tut_date_1[1]))
            data = data.replace('TOREPLACE_TUT_DATE_B', "(%s, %s)" % (tut_date_2[0], tut_date_2[1]))
            data = data.replace('TOREPLACE_TUT_DATE_C', "(%s, %s)" % (tut_date_3[0], tut_date_3[1]))
        else:
            # otherwise don't show the single date (since it's in title)
            data = data.replace('TOREPLACE_TUT_DATE_A', "")
            data = data.replace('TOREPLACE_TUT_DATE_B', "")
            data = data.replace('TOREPLACE_TUT_DATE_C', "")

    with open(final_tex_path, 'wt') as f:
        f.write(data)

# Generate final file used for generation final/UTC+x/handbook.tex
print "=================generating final handbook.tex"
# copy a base tex file
final_tex_path = 'handbook_%s.tex' % args.timezone
if os.path.exists(final_tex_path):
    os.remove(final_tex_path)
copyfile(args.base_handbook_tex, final_tex_path)

# replace some key parameters
with open(final_tex_path, 'rt') as f:
    data = f.read()
    data = data.replace('TOREPLACE_TIMEZONE', args.timezone)

with open(final_tex_path, 'wt') as f:
    f.write(data)

out = open(final_tex_path, 'a')

if args.sec_tutorials:
    # add content to final tex, tutorial part
    print >>out, '\setdaydateyear{%s}{%s}{%s}' % (tut_final_day, tut_final_date, tut_final_year)
    print >>out, '\input{content/tutorials/%s/tutorials-overview}' % args.timezone

if args.sec_papers:
    # add content to final tex, main conference part
    # for day_i, date in enumerate([dates[0]]):
    for day_i, date in enumerate(dates):
        print(date)
        day, num, year = date

        print >>out, '\\setdaydateyear{%s}{%s}{%s}' % (day, num, year)
        print >>out, '\\input{%s/day%d}' % (day_summary_output_dir_timezone, (day_i + 1))
        print >>out, '\\newpage'

# add content to final tex, workshop part
if args.sec_workshops:
    print >>out, '\\input{content/workshops/%s/workshops}' % args.timezone

# add content to final tex, misc part
print >>out, '\\input{content/anti-harassment-policy}'
print >>out, '\\newpage'

print >>out, '\\input{content/author-guidelines}'
print >>out, '\\newpage'

print >>out, '\\cleardoublepage'
print >>out, '\\addcontentsline{toc}{chapter}{Author Index}'
print >>out, '\\setheaders{Author Index}{Author Index}'
print >>out, '\\printindex'

# add content to final tex, sponsors part
print >>out, '\\addcontentsline{toc}{chapter}{Sponsorship}'
print >>out, '\\setheaders{}{}'
print >>out, '\\input{content/ads/ads_logo}'

print >>out, '\\end{document}'
out.close()
