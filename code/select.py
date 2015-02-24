#!/usr/bin/env python

'''
Given two files, select (output) lines of the second (data) file which contain one of
the data items in the first (selector) file.
'''
from __future__ import print_function
from collections import namedtuple
from optparse import OptionParser
import sys

LINEEND = '\r\n'   # for rstrip
FIELDSEP = '\t'    # for split

error_log = sys.stderr

def main():
    useage = '''useage:
    %prog [-s [name|number] selector_file [-c [name|number] data_file [-o output_file]"
    
    Given two input files, the values of a specified column of
     a selector file will be used to select output.
    Data in the specified "compare" column of the data_file will
     be checked against the selector data.
    If a compare data item from the data_file exists in the selector set,
     then that data_file row (line) will be output.
    
    You may also specify an output file.
     
    - If a field name is given, the first line of the file
      is assumed to contain field names.
    - If a field number is given, the n-th field is used (left-to-right,
      beginning with 1); all lines are assumed to be data
    - Fields are assumed to be TAB separated.
    
    
    example:
    % select -s IID relationships.txt -c 2 some.ped -o filtered.ped
    
    This will use the "IID" column from relationships.  Any row in "some.ped"
    which has column-2 data matching an IID data will be output to "filtered.ped"
    
    This is equivalent:
    % select -sIID relationships.txt -c2 some.ped -ofiltered.ped
    
    '''
    parser = OptionParser(useage)

    parser.add_option( "-s", "--select-column", dest="select_column",
                       help="column from which to build selection matching data")
    parser.add_option( "-c", "--compare-column", dest="compare_column",
                       help="column to compare against selection criteria")
    parser.add_option( "-o", "--output", dest="output",
                       help="output file for selected data")

    (options,args) = parser.parse_args()
    output = options.output
    select_column = proper_type(options.select_column)
    compare_column = proper_type(options.compare_column)
    compare_asindex = type(compare_column) is int

    if (select_column is None) or (compare_column is None):
        error_log.write("Need to specify select column (-s) and compare column (-c).\nTry -h option for help.\n")
        exit(1)
    if len(args)<2:
        parser.print_help()
        exit(1)

    fname = args[0]
    fp = sys.stdin if fname == '-' else must_open(fname)
    fo = sys.stdout if output is None else must_open(output, 'w')
    selectors = get_selectors(fp, select_column)
    if type(select_column) is int:
        select_column -= 1  # adjust for zero-based array indexing

    for fname in args[1:]:
        global n
        n = 0
        fp = sys.stdin if fname == '-' else must_open(fname)
        line = fp.readline()
        # assume first line is a header line, if named data field:
        if not compare_asindex:
            dat = namedtuple("dat", line.rstrip(LINEEND).split(FIELDSEP))
            line = fp.readline()
        else:
            maxsplit = compare_column
            compare_column -= 1   # i.e. 2nd column => row[1]
        while not (line == ''):
            n+=1
            # split the line fields
            if compare_asindex:
                line_element = line.rstrip(LINEEND).split(FIELDSEP, maxsplit)
            else:
                drow = dat(*line.rstrip(LINEEND).split(FIELDSEP))
                line_element = drow._asdict()
            
            # output if the specified data field is in the selector
            if line_element[compare_column] in selectors:
                fo.write(line)
            line = fp.readline()


def get_selectors(fp, column):
    '''
    using the global option, select a column from the file, and return a dict (hash performance) with all the values
    '''
    selectors = {}
    # Get column option:
    # - if numeric, split the fields and use number as an index,
    # - else use named.tuples, and use the first line as the header
    asindex = type(column) is int
    if not asindex:
        # get the first line, which we expect to be the column header
        line = fp.readline()
        hdr = namedtuple("hdr", line.rstrip(LINEEND).split(FIELDSEP))
    else: # can only limit splits on numerics
        maxsplit = column
        column -= 1   # i.e. 2nd column => row[1]
    # now go thru the file:
    line = fp.readline()
    while not (line==''):
        # prepare so we index correctly either way:
        if asindex:
            row = line.rstrip(LINEEND).split(FIELDSEP, maxsplit)
        else:
            drow = hdr(*line.rstrip(LINEEND).split(FIELDSEP))
            row = drow._asdict()
        selectors[row[column]]=''   # we only care about key, not value
        line = fp.readline()
    return selectors

def must_open(f, c='r'):
    try:
        fp = open(f,c)
    except IOError as e:
        error_log.write('Unable to open %s : %s\n' % (f,e))
        exit(2)
    return fp

def proper_type(i):
    return int(i) if (i and i.isdigit()) else i

if __name__=='__main__':
    main()