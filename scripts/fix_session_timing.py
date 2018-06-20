"""
Author:         Jey Han Lau
Date:           Jun 18
"""

import argparse
import sys

#parameters
debug = True

###########
#functions#
###########

def is_paper_line(line):

    try:
        x = int(line.split()[0].split("/")[0])
        return True
    except:
        return False

def add_time_to_session(lines):

    if "--" in lines[0][2:].split()[0]: #session already has timing information
        return lines

    else:
        fixed = []
        start = lines[1].split()[1].split("--")[0]
        end = lines[-1].split()[1].split("--")[-1]

        fixed.append("= " + start + "--" + end + lines[0][1:])
        fixed.extend(lines[1:])

        return fixed
        

######
#main#
######

def main(args):

    out = open(args.output, "w")
    in_session = False
    acc_lines = []

    for line in open(args.input):

        line = line.strip()

        if not in_session:

            if line.startswith("="):
                in_session = True
                acc_lines.append(line)
            else:
                out.write(line + "\n")

        else: #in session
        
            if is_paper_line(line):
                acc_lines.append(line)
            else:
                fixed_lines = "\n".join(add_time_to_session(acc_lines))
                out.write(fixed_lines + "\n")
                acc_lines = []
                in_session = False
                out.write(line + "\n")

    if in_session:
        fixed_lines = "\n".join(add_time_to_session(acc_lines))
        out.write(fixed_lines + "\n")

    out.flush()
    out.close()
            

if __name__ == "__main__":

    #parser arguments
    desc = "inserts time range for talk sessions in order files, if they are missing"
    parser = argparse.ArgumentParser(description=desc)

    #arguments
    parser.add_argument("-i", "--input", help="input order file")
    parser.add_argument("-o", "--output", help="output fixed order file")
    args = parser.parse_args()

    main(args)
