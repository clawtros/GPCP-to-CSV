#!/usr/local/bin/python2.6
"""
Purpose
-------
    Takes an input binary file of a well know format, extracts the data and
    saves it in a simple but required CSV format.

Program Flow
------------
    Input:
        A file name with the full location,
        i.e. C:\Users\schiefej\Desktop\binary_filename.bin

    Output:
        Writes data to an output CSV file in the format per line of:
        YYYYMMDD,latitude,longitude,value
        where YYYY is the year in four digits, MM is the month in two digits
        and DD is the day in two digits.


Notes/Lessons Learned
---------------------
    None

--------

"""
#------------------------------------------------------------------------------
#     Imports
#------------------------------------------------------------------------------


# The __future__ print function is used to ensure an easier path to
# Python 3 if and when the upgrade is needed.
from __future__ import print_function

# built-ins
import argparse
import cProfile
import datetime
import gzip
import logging
import os
import pstats
import StringIO
import sys
import time

# external
import gpcp_parsers

#------------------------------------------------------------------------------
#     Functions
#------------------------------------------------------------------------------


def get_args():
    """
    Purpose
        Get the command line arguments and provide help if the -h option is
        selected.

    Returns
        A tuple in a format similar to:
            Namespace(input_file='C:/Users/schiefej/Desktop/gpcp_v2.2psg.1987',
                      output_file='C:/Users/schiefej/Desktop/out_1987',
                      input_prefix='',
                      output_prefix='',
                      years='[]')
        or
            Namespace(input_file='',
                      output_file='',
                      input_prefix='gpcp_v2.2psg.',
                      output_prefix='gpcp_out_',
                      years='(1987,2011)')

    """
    parser = argparse.ArgumentParser()

    parser.add_argument('-z',
                        '--gzip',
                        action='store_true',
                        help="Set this flag if the input files are " + \
                             "zipped using gzip and end with .gz.")

    parser.add_argument('-s',
                        '--single_file',
                        action='store_true',
                        help="Set this flag if running the program for " + \
                             "only a single (one) file.  Then provide the " + \
                             "input_file.")

    parser.add_argument('-i',
                        '--input_file',
                        default="",
                        help="The full path of the input file, i.e.: " + \
                             "C:/Users/schiefej/Desktop/gpcp_v2.2psg.1987" + \
                             " if no year(s) is(are) provided this is " + \
                             "required.")

    parser.add_argument('-o',
                        '--output_file',
                        default="",
                        help="The full path of the input file, i.e.: " + \
                             "C:/Users/schiefej/Desktop/out_1987.csv")

    parser.add_argument('-p',
                        '--input_prefix',
                        default="./gpcp_1dd_v1.2_p1d.",
                        help="The path to the input file(s) and " + \
                             "the appropriate prefix such as: " + \
                             "'./gpcp_v2.2_psg.' or " + \
                             "'C:/Users/schiefej/binary_files/gpcp_file_'" + \
                             "The default is the current directory plus " + \
                             "the prefix for the new format files: " + \
                             "'./gpcp_1dd_v1.2_p1d.'")

    parser.add_argument('-op',
                        '--output_prefix',
                        default="./gpcp_out_",
                        help="The path to the output file(s) and " + \
                             "the appropriate prefix such as: " + \
                             "'./gpcp_out_' or " + \
                             "'C:/Users/schiefej/binary_files/gpcp_out_'")

    current_year = datetime.datetime.now().year
    parser.add_argument('-y',
                        '--years',
                        default=str(current_year),
                        help="Years of the requested data, i.e. 2012" + \
                             " or 1987,2011.  The MUST be no spaces in " + \
                             "the string, ie. 1999,2000 is okay but " + \
                             "1999, 2000 is not." + \
                             "This is a optional value but if it is " + \
                             "provided, prefixes must be provided.  If  " + \
                             "it is provided, an input file must be provided.")

    current_month = datetime.datetime.now().month
    parser.add_argument('-m',
                        '--months',
                        default=str(current_month),
                        help="Months of the requested data, i.e. 10 " + \
                             "or 1,2,3,4,5,6,7,8,9,10,11,12 for an " + \
                             "entire year.  There MUST be no spaces in " + \
                             "the string; see the year argument for " + \
                             "applicable examples but using month numbers.")

    parser.add_argument('-f',
                        '--format',
                        default='2',
                        help="The output format determines which parser " + \
                             "to use. 0 is for the version one format and " + \
                             "map CSV output. 1 is for single line " + \
                             "CSV output with the version one file format." + \
                             " 2 is the default and is for single line " + \
                             "CSV output with the version 2 file format.")

    return parser.parse_args()

#------------------------------------------------------------------------------


def check_args(args):
    """ Checks the validity of the inputs from the command lines.

    Input:
        A tuple of arguments from the command line

    Output:
        Returns a tuple with the verified/checked values.  Exits if values
        are not correct with the appropriate error message.

    """
    # get the known arguments from args
    zipped = args.gzip
    single_file = args.single_file
    input_file = args.input_file
    output_file = args.output_file
    input_prefix = args.input_prefix
    output_prefix = args.output_prefix
    years = args.years
    months = args.months
    format_opt = args.format

    if single_file:
        # check for input_file and output_file
        if input_file != "" and output_file != "":
            format_opt = int(format_opt)

            return (zipped,
                    input_file,
                    output_file,
                    format_opt)
        else:
            err_message = "For a single file, a input and output file " + \
                          "must be specified with the appropriate options."
            error_help_then_exit(err_message)

    else:  # multi_file options
        format_opt = int(format_opt)
        if not(0 <= format_opt <= 2):
            err_message = "Please enter an appropriate format option with " + \
                          "-f as in:  "
            error_help_then_exit(err_message)

        years_list = []
        if "," in years:
            years_list = years.split(",")
        else:
            years_list.append(years)
        for year in years_list:
            if not(1970 <= int(year) <= int(datetime.datetime.now().year)):
                err_message = "Please enter a year from 1970 to current."
                error_help_then_exit(err_message)

        if format_opt != 0:
            months_list = []
            if "," in months:
                months_list = months.split(",")
            else:
                months_list.append(months)
            for month in months_list:
                if not(1 <= int(month) <= 12):
                    err_message = "Please enter a month from 1 to " + \
                                  "12 inclusive."
                    error_help_then_exit(err_message)
        else:
            months_list = None

        return (zipped,
                input_prefix,
                output_prefix,
                years_list,
                months_list,
                format_opt)

#------------------------------------------------------------------------------


def error_help_then_exit(message):
    """ Prints the given message, then has the help for the program print
    out and then exits.

    """
    print(message)
    os.system("python -B gpcp_to_csv.py -h")
    sys.exit()


#------------------------------------------------------------------------------


def unzip(filename):
    """ Unzips a gzip file for use.  If the file ends with .gz it decompresses
    the file to the filename minus the .gz file extension.  If the file does
    not end with .gz it adds _unzipped at the end of the file name.

    Input:
        The file name of a compressed file.  The file must be compressed using
        gzip.

    Returns:
        The file name of the uncompressed file.

    """
    if filename.endswith(".gz"):
        return_filename = filename[:-3]
    else:
        return_filename = filename + "_unzipped"

    try:
        z_content = gzip.open(filename, 'rb')
        print("\nExtracting data from: ", filename)
        with open(return_filename, 'wb') as uncompressed:
            uncompressed.write(z_content.read())

    except IOError, error:
        print("\nIOError from unzip: ", error)
        raise

    else:
        return return_filename

#------------------------------------------------------------------------------


def process_file(input_filename, output_filename, format_opt, zipped):
    """ Extracts the data from the input file and saves it in CSV format in
    the output file in the format specified by the format option.  If the file
    is zipped it is decompressed first.

    """
    if zipped:
        try:
            input_file = unzip(input_filename)

        except IOError:
            err_message = "Skipping file: " + input_filename + "\n"
            print(err_message)
            return 0

    else:
        input_file = input_filename

    if format_opt == 0:
        parser = gpcp_parsers.GpcpParserOriginal(input_file)
    elif format_opt == 1:
        parser = gpcp_parsers.GpcpParserOriginalOneLine(input_file)
    elif format_opt == 2:
        parser = gpcp_parsers.GpcpParserNewOneLine(input_file)
    else:
        err_message = "An incorrect format was entered please enter a " + \
                      "valid option of 0, 1, or 2."
        error_help_then_exit(err_message)

    if parser.has_data():
        with open(output_filename, 'w') as out_file:
            print("Writing CSV value to ", output_filename)
            parser.write_csv(out_file)

    if zipped:
        os.remove(input_file)

    return 1

#------------------------------------------------------------------------------
#     Main
#------------------------------------------------------------------------------


def main():
    """ The 'main' function used to run the file/modules as a stand alone
    application.

    """
    # get the arguments, parse and then check them
    the_args = check_args(get_args())

    # set some variables for program readability
    num_of_args = len(the_args)
    num_of_singlefile_args = 4  # this will change with changes to check_args
    num_of_multifile_args = 6  # ditto for this number

    # for single file
    if num_of_args == num_of_singlefile_args:
        zipped, input_file, output_file, format_opt = the_args
        print("\nStarting process to reformat GPCP binary data to CSV.")

        if not(output_file.endswith(".csv")):
            output_file = output_file + ".csv"

        process_file(input_file, output_file, format_opt, zipped)

        print("\nProcess complete.\n")

    # for multiple files
    elif num_of_args == num_of_multifile_args:
        (zipped,
         input_prefix,
         output_prefix,
         years,
         months,
         format_opt) = the_args

        files_dict = {}
        for year in years:
            if format_opt != 2:
                if zipped:
                    in_file = input_prefix + year + ".gz"
                else:
                    in_file = input_prefix + year

                out_file = output_prefix + year + ".csv"
                files_dict[in_file] = out_file

            else:
                for month in months:
                    month = month.zfill(2)
                    if zipped:
                        in_file = input_prefix + year + month + ".gz"
                    else:
                        in_file = input_prefix + year + month

                    out_file = output_prefix + year + month + ".csv"
                    files_dict[in_file] = out_file

        print("\nStarting process to reformat GPCP binary data to CSV.")

        for input_file, output_file in sorted(files_dict.iteritems()):
            process_file(input_file, output_file, format_opt, zipped)

        print("\nProcess complete.\n")

    # there was an error, the program should never get here
    else:
        print("There was a significant error not caught elsewhere. " + \
              "Try again, if it happens again then submit a bug report.")


def profile_main():
    """
    Purpose
        Used from if __name__ == ... to profile the program from the command
        line and locate the bottlenecks

        Profiles the main() function and logs the result to a file.  This file
        is simply text and can be viewed using a simple text editor.  At a
        later time it might be beneficial to create a html or
        reStructured text file for easier reading.

        Got idea and code from:
            http://code.google.com/appengine/kb/commontasks.html#profiling

    Input
        Same as main(), defined in previous function.

    Output
        A text file name profile_filename_timestamp.log containing a full
        profile of calls and timing.

    """
    # get and format the time stamp for the file name
    today = str(datetime.date.fromtimestamp(time.time()))
    now = str(int(time.time() * 100))[6:]  # for a unique file name

    # define the file name
    file_name = (os.path.basename(__file__))[:-3]
    profile_log_name = "profile_" + file_name + "_" + \
                       today + "_" + now + ".log"

    # begin logging
    logging.basicConfig(filename=profile_log_name, level=logging.DEBUG)

    # start profiling
    profiler = cProfile.Profile()
    profiler = profiler.runctx("main()", globals(), locals())

    stream = StringIO.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats("time")

    # Or cumulative
    stats.print_stats(160)  # 80 = how many to print
    # The rest is optional.
    # stats.print_callees()
    # stats.print_callers()
    logging.info("Profile data:\n%s", stream.getvalue())

#------------------------------------------------------------------------------
#     Name
#------------------------------------------------------------------------------


if __name__ == '__main__':
    main()
    # profile_main()
