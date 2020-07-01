# -*- coding: utf-8 -*-

import re
from csv import DictReader

def extract_keywords(title):
    """Extracts keywords from a title, and returns the title and a dictionary of keys and values"""
    dict = {}
    for key, value in re.findall('%(\w+) ([^%]+)', title):
        dict[key] = value

    if title.find('%') != -1:
        title = title[:title.find('%')].strip()

    return title, dict
        
def latex_escape(str):
    """Replaces unescaped special characters with escaped versions, and does
    other special character conversions."""
    
    str = str.replace('~','{\\textasciitilde}')
#    str = str.replace('β','\\beta')

    # escape these characters if not already escaped
    special_chars = r'\#\@\&\$\_\%'
    patternstr = r'([^\\])([%s])' % (special_chars)
    str = re.sub(patternstr, '\\1\\\\\\2', str)

    # fix superscripts
#    str = re.sub(r'([^$])\^(.*?) ', r'\1$^\2$ ',  str)
    return str

day_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

def timezone_convert(time, date_tuple, origin_tz, target_tz):
    day, date, year = date_tuple
    time_diff = int(target_tz[3:]) - int(origin_tz[3:])
    time_start = int(time.split('--')[0].split(':')[0])
    time_end = int(time.split('--')[1].split(':')[0])

    time_start_new = time_start + time_diff
    time_end_new = time_end + time_diff
    date_new = date
    day_new = day

    if time_end_new <= 0:
        date_new = date.split(' ')[0] + ' ' + str(int(date.split(' ')[1]) - 1)
        time_start_new = time_start_new + 24
        time_end_new = time_end_new + 24
        day_new = day_list[(day_list.index(day) - 1) % 7]

    if time_start_new >= 24:
        date_new = date.split(' ')[0] + ' ' + str(int(date.split(' ')[1]) + 1)
        time_start_new = time_start_new - 24
        time_end_new = time_end_new - 24
        day_new = day_list[(day_list.index(day) + 1) % 7]

    # deal with the cases like 24:15
    if time_end_new >= 24:
        time_end_new_str = str(time_end_new-24) + ':' + time.split('--')[1].split(':')[1] + ' (+1)'
    else:
        time_end_new_str = str(time_end_new) + ':' + time.split('--')[1].split(':')[1]

    time_new = str(time_start_new) + ':' + time.split('--')[0].split(':')[1] + '--' + time_end_new_str
    return time_new, (day_new, date_new, year)

class Paper:
    def __init__(self, line, subconf):
        self.id, rest = line.split(' ', 1)
        if re.match(r'^\d+', rest) is not None:
            self.time, comment = rest.split(' ', 1)
            self.poster = False
        else:
            self.time = None
            self.poster = True
            comment = rest

        if self.id.find('/') != -1:
            tokens = self.id.split('/')
            if tokens[1] == 'SRW':
                self.id = '%s-%s' % (tokens[1], tokens[0])
            else:
                self.id = '%s-%s' % (tokens[1].lower(), tokens[0])
        else:
            self.id = '%s-%s' % (subconf, threedigits(self.id))
            
    def __str__(self):
        return "%s %s" % (self.id, self.time)

def threedigits(str):
    return '%03d' % (int(str))

class Session:
    def __init__(self, line, date, origin_tz='UTC+0', target_tz="UTC+0"):
        (self.time, namestr) = line[2:].split(' ', 1)
        self.date = date
        self.papers = []
        self.desc = None

        # this day, date, and year will be used by following code section.
        # Timezone convertion
        print '====='
        print self.time, self.date
        self.time, self.date = timezone_convert(self.time, self.date, origin_tz, target_tz)
        print self.time, self.date

        (self.name, self.keywords) = extract_keywords(namestr)
        
        if self.name.find(':') != -1:
            colonpos = self.name.find(':')
            self.desc = self.name[colonpos+2:]
            self.name = self.name[:colonpos]
            self.num = self.name.split(' ')[-1][:-1]
        else:
            match = re.search("Session (\d+[a-zA-Z]+)", self.name)  
            if match != None:
                # extract more information from the line
                # session title like "Vision, Linguistics, Resource and Evaluation (Short)"
                self.desc = self.name[match.end()+1:]
                if 'Demo Session' not in line:
                    # sessopm name like "Session 5E"
                    self.name = match.group(0)
                    # parallel session number, like "5"
                    self.num = match.group(1)
                else:
                    # Demo session. 2020's demo session use same session name and num multiple times, like Demo Session 1A appear 3 times. So need to distinguish them
                    self.name = self.name
                    self.num = '%s-demo-%s' % (self.date[0], match.group(1))

        # print >> sys.stderr, "LINE %s NAME %s DESC %s" % (line, self.name, self.desc)

        self.poster = False
        l = self.name.lower()
        if 'poster' in l or 'demo' in l or 'best paper' in l:
            self.poster = True

    def __str__(self):
        return "SESSION [%s/%s] %s %s" % (self.date, self.time, self.name, self.desc)

    def add_paper(self,paper):
        self.papers.append(paper)

    def chair(self):
        """Returns the (first name, last name) of the chair, if found in a %chair keyword"""
        
        if self.keywords.has_key('chair'):
            fullname = self.keywords['chair']
            if ',' in fullname:
                names = fullname.split(', ')
                return (names[1].strip(), names[0].strip())
            else:
                # This is just a heuristic, assuming the first name is one word and the last
                # name is 1+ words
                names = fullname.split(' ', 1)
                return (names[0].strip(), names[1].strip())
        else:
            return ('', '')

