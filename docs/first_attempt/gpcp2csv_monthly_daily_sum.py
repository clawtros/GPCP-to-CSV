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

import argparse
import cProfile
import cStringIO    # Provides a way write to a memory file and then dump to
                    # the file all at once rather than one line at a time.
                    # This has proven to be faster than using the CSV writer.
import datetime
import gzip
import logging
import os
import pstats
import StringIO
import struct
import sys
import time

#------------------------------------------------------------------------------
#     Class:  Coord and derived classes Lat, Lon and LatLon
#------------------------------------------------------------------------------


class Coord(object):
    """ For printing a coordinate, i.e. the value (i.e. where) and
    direction.

    """
    def __init__(self,
                 string_representation=None,
                 point=None,
                 direction=None):
        """ The initialization function """
        if string_representation:
            direction = string_representation[-1].upper()

            modifier = 1
            if direction in ('S', 'W'):
                modifier = -1
                direction = 'N' if direction.upper() == 'S' else 'E'

            self.direction = direction
            self.point = modifier * float(string_representation[0:-1])

        elif point and direction:
            self.direction = direction
            self.point = point
        else:
            err_str = "must supply string representation " + \
                      "or both point and direction"
            raise ValueError(err_str)

    def __str__(self):
        """ Descibes what to print when the object is printed. """
        return "%f%s" % (self.point, self.direction)

    def get_coord(self):
        """ Returns the coordinate as a tuple: (coord, direction). """
        return (self.point, self.direction)

    def get_point(self):
        """ Returns the point. """
        return self.point

    def get_direction(self):
        """ Returns the direction. """
        return self.direction


class Lat(Coord):
    """ Inherits from Coord and is the latitude part of a full coordinate. """
    def __init__(self, point):
        """ The initialization function """
        Coord.__init__(self, string_representation=str(point))
        self.point = point

    def __str__(self):
        """ Print the 'object'. """
        return "%0.2f%s" % \
               (self.point \
                if self.point > 0 \
                else (-1 * self.point), "N" if self.point > 0 else "S")


class Lon(Coord):
    """ Inherist from Coord and is the longitude part of a full coordinate. """
    def __init__(self, point):
        """ The initialization function """
        Coord.__init__(self, string_representation=str(point))
        self.point = point

    def __str__(self):
        """ Descibes what to print when the object is printed. """
        return "%0.2f%s" % \
               (self.point \
                if self.point > 0 \
                else (-1 * self.point), "E" if self.point > 0 else "W")


class LatLon(object):
    """ A full coordinate point combining a latitdue/longitude point. """
    def __init__(self, lat, lon):
        """ The initialization function """
        self.lat = lat
        self.lon = lon

    def delta_to(self, other_coord):
        """ The difference or distance between two LatLon points. """
        return (abs(self.lat.point - other_coord.lat.point),
                abs(self.lon.point - other_coord.lon.point))

    def __str__(self):
        """ Describes what to print when the object is printed. """
        return "%s %s" % (str(self.lat), str(self.lon))

    def get_lat(self):
        """ Returns the latitude of the LatLon. """
        return self.lat

    def get_lon(self):
        """ Returns the longitude of the LatLon. """
        return self.lon

#------------------------------------------------------------------------------
#     Class:  GeoMap
#------------------------------------------------------------------------------


class GeoMap(object):
    """ Defines a map area and associated string for printing. """
    def __init__(self,
                 topleft,
                 next_point,
                 _bottomright,
                 points_per_row,
                 rows):
        """ The initialization function """
        self.map = []
        self.topleft = topleft
        map_lat = topleft.lat.point
        _start_lat = topleft.lat.point
        start_lon = topleft.lon.point

        delta = max(topleft.delta_to(next_point))

        for _i_counter in range(rows):
            row = []
            map_lon = start_lon
            for _j_counter in range(points_per_row):
                row.append(LatLon(Lat(map_lat), Lon(map_lon)))
                map_lon += delta
            self.map.append(row)
            map_lat += -1 * delta

    def __str__(self):
        """ For printing the instance of the object. """
        return "\n".join([", ".join([str(ll) for ll in row]) \
                          for row in self.map])

    def get_start_lat(self):
        """ Returns the starting latitude coordinate. """
        return self.topleft.lat.point

    def get_start_lon(self):
        """ Returns the starting longitude coordinate. """
        return self.topleft.lon.point


#------------------------------------------------------------------------------
#     Class:  GpcpParser
#------------------------------------------------------------------------------


class GpcpParser(object):
    """ Takes an input file name and then writes output to a CSV. """
    def __init__(self, filename):
        """ The initialization function for an object.
            filename:
                The name of the input file.
            zipped:
                A boolean (True/False) if the file in filename is zipped by
                gzip.
        """
        # Ensure data and header variables are reset, critical for looping
        # over a GpcpParser.
        self.data = []
        self.header = ""

        # Get the variables from the first line of the file
        self.variables = self.get_variables(filename)
        if self.variables == 0:
            return

        try:
            with open(filename, 'rb') as handle:
                self.header = handle.read(int(self.variables["row_size"]))
                things_per_row = \
                    int(self.variables["row_size"]) / \
                    int(self.variables["thing_size"])

                # Per documentation for file structure the floats are
                # big-endian
                # struct uses ">" to determine byte order.  "f" is for float
                row_format = ">" + "f" * things_per_row
                while True:
                    packed = handle.read(int(self.variables["row_size"]))
                    if packed:
                        row = struct.unpack(row_format, packed)
                        self.data.append(row)
                    else:
                        break
        except IOError, error:
            print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print("IOError: ", error)
            print("Skip READING file: ", filename)

    def generate_map(self):
        """ Generates the needed map and returns it. """
        pstr = self.header[self.header.index('1st_box_center'):]
        start_pstr = LatLon(*[Coord(p) \
                         for p in pstr[pstr.index('(') + \
                                       1:pstr.index(')')].split(',')])

        pstr = pstr[pstr.index('2nd_box_center'):]
        next_pstr = LatLon(*[Coord(p) \
                        for p in pstr[pstr.index('(') + \
                                      1:pstr.index(')')].split(',')])

        pstr = pstr[pstr.index('last_box_center'):]
        end_pstr = LatLon(*[Coord(p) \
                       for p in pstr[pstr.index('(') + \
                                     1:pstr.index(')')].split(',')])

        coords = GeoMap(start_pstr,
                        next_pstr,
                        end_pstr,
                        int(self.variables["points_per_row"]),
                        int(self.variables["rows_per_day"]))

        # This is where some math using 1st_box_center should be done to
        # determine the correct value to add/subtract.  For the current
        # files being used it is 360, but this might not always be the case.
        coords_map = []
        for line in coords.map:
            for coord in line:
                latitude, longitude = str(coord).split(" ")
                if latitude[-1] == "S":
                    latitude = float("-" + latitude[:-1])
                else:
                    latitude = float(latitude[:-1])

                longitude = float(longitude[:-1])
                if longitude < 180:
                    longitude = longitude
                else:
                    longitude = longitude - 360

                coords_map.append([latitude, longitude])

        return coords_map

    @staticmethod
    def get_variables(inputfile):
        """ Gets variables from the header. """
        # Define the dictionary for returning values from the file
        variables = {"file": "",
                     "title": "",
                     "size": "",
                     "row_size": "",
                     "points_per_row": "",
                     "thing_size": "",
                     "version": "",
                     "variable": "",
                     "units": "",
                     "missing_value": "",
                     "creation_date": "",
                     "year": "",
                     "month": "",
                     "days": "",
                     "rows_per_month": "",
                     "grid": "",
                     "dimensions": "",
                     "1st_box_center": "",
                     "2nd_box_center": "",
                     "last_box_center": ""
                    }

        # Open the file, inputfile, and read only the first line
        try:
            with open(inputfile, "r") as the_input:
                first_line = the_input.readline()

        except IOError, error:
            print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print("IOError: ", error)
            print("Skip READING file: ", inputfile)
            return 0

        else:
            # Get the values from the first line of the 'inputfile'
            for item in first_line.split(" "):
                if item.startswith("(real"):
                    variables["dimensions"] = item
                else:
                    for var, _value in variables.iteritems():
                        if item.startswith(var):
                            variables[var] = (item.split("="))[1]
                            break

            # Calculate values from the variables in variables
            variables["row_size"] = variables["size"].split("*")[1][:-1]
            variables["thing_size"] = \
                (variables["dimensions"].split("x")[0]).split("*")[1][:-1]
            variables["points_per_row"] = \
                (variables["dimensions"].split("x")[1])
            variables["start_day"], variables["end_day"] = \
                variables["days"].split("-")
            variables["rows_per_day"] = variables["dimensions"].split("x")[2]

            # Adjust lat/lon values from 1st, 2nd and last boxes. Negatives are
            # S and W.  Positives N and E.  Put in values that are floats, but
            # leave as tuples.
            for geo_point in ["1st_box_center",
                              "2nd_box_center",
                              "last_box_center"]:
                n_or_s = (variables[geo_point].split(","))[0][-1]
                if n_or_s == "N":
                    box_lat = \
                        float((variables[geo_point].split(","))[0][1:-1])
                else:
                    box_lat = \
                        float("-" + (variables[geo_point].split(","))[0][1:-1])

                e_or_w = (variables[geo_point].split(","))[1][-2]
                if e_or_w == "E":
                    box_lon = \
                        float((variables[geo_point].split(","))[1][0:-2])
                else:
                    box_lon = \
                        float("-" + (variables[geo_point].split(","))[1][0:-2])

                variables[geo_point] = box_lat, box_lon

            return variables

    def has_data(self):
        """ Returns True if there is data in self.data, False otherwise. """
        return len(self.data) > 0

    def write_csv(self, handle):
        """ Writes out the csv data using the cStringIO module.  """
        # Create a cStingIO object.  Write to the memory 'file' and then
        # in the last line of the function write the entire memory 'file' to
        # disk all at once.
        file_str = cStringIO.StringIO()
        coords = self.generate_map()

        coord_pos = 0
        for idx, row in enumerate(self.data):
            if (idx % int(self.variables['rows_per_day']) == 0):
                arbitrary_date = datetime.date(int(self.variables['year']),
                             int(self.variables['month']),
                             idx / int(self.variables['rows_per_day']) + 1)
                the_date = (self.variables["year"] + \
                            self.variables["month"] + \
                            arbitrary_date.strftime("%d"))

                # Reset to top of 'map' (i.e. the beginning of the coordinate
                # list) at the beginning of each month.
                coord_pos = 0

            for element in row:
                # The "$4.2f" is for floating point, it rounds correctly and
                # if more decimal places are needed change the 2 to a higher
                # number.
                value = "%4.2f" % element

                # Each row of requested output should be:
                # data, lat, lon, value
                file_str.write(str(the_date) + "," + \
                               str(coords[coord_pos][0]) + "," + \
                               str(coords[coord_pos][1]) + "," + \
                               str(value) + "\n")
                coord_pos += 1

        handle.write(file_str.getvalue())

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
                             "zipped using zip and end with .gz.")

    parser.add_argument('-i',
                        '--input_file',
                        default="",
                        help="The full path of the input file, i.e.: " + \
                             "C:/Users/schiefej/Desktop/gpcp_v2.2psg.1987" + \
                             " if no year(s) is(are) provided this is " + \
                             "required.")

    parser.add_argument('-o',
                        '--output_file',
                        default="./gpcp_out_",
                        help="The full path of the input file, i.e.: " + \
                             "C:/Users/schiefej/Desktop/out_1987.csv " + \
                             "The default is: ./gpcp_out_")

    parser.add_argument('-p',
                        '--input_prefix',
                        default="",
                        help="The path to the input file(s) and " + \
                             "the appropriate prefix such as: " + \
                             "'./gpcp_v2.2_psg.' or " + \
                             "'C:/Users/schiefej/binary_files/gpcp_file_'")

    parser.add_argument('-op',
                        '--output_prefix',
                        default="",
                        help="The path to the output file(s) and " + \
                             "the appropriate prefix such as: " + \
                             "'./gpcp_out_' or " + \
                             "'C:/Users/schiefej/binary_files/gpcp_out_'")

    parser.add_argument('-y',
                        '--years',
                        default="()",
                        help="Years of the requested data, i.e. (2012)" + \
                             " or (1987,2011).  The MUST be no spaces in " + \
                             "the string, ie. (1999,2000) is okay but " + \
                             "(1999, 2000) or ( 1999,2000 ) are not." + \
                             "This is a option value if filled in prefixes" + \
                             " must be provided, if it is not an input" + \
                             " file must be provided.")

    parser.add_argument('-m',
                        '--months',
                        default="()",
                        help="Months of the requested data, i.e. (10) " + \
                             "or (1,2,3,4,5,6,7,8,9,10,11,12) for an " + \
                             "entire year.  There MUST be no spaces in " + \
                             "the string; see the year argument for " + \
                             "applicable examples but using month numbers.")

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
    input_file = args.input_file
    output_file = args.output_file
    input_prefix = args.input_prefix
    output_prefix = args.output_prefix
    years = args.years
    months = args.months
    zipped = args.gzip

    # print input_file, output_file, input_prefix, output_prefix, years

    # Convert years string into a list of years
    years = years[1:-1].split(",")
    months = months[1:-1].split(",")

    if ((len(years) == 1 and len(years[0]) == 0) and
         (len(months) == 1 and len(months[1]) == 0)):
        single_file = True
    else:
        single_file = False

    if single_file:
        if input_file == "":
            print("There is not a default value for the input file.  ",
                  "Please give a value for the input file that is a full ",
                  "file name including the path, i.e. ",
                  "C:/Users/schiefej/Desktop/gpcp_v2.2_psg.1987")
            sys.exit()

        if output_file == "":
            print("Using default value for the output: ./gpcp_out.csv")
            output_file = "./gpcp_out.csv"

        if input_prefix != "":
            print("Ignoring input prefix value of: ", input_prefix)
            print("If you want to use it ensure a year(s) value is provided.")

        if output_prefix != "":
            print("Ignoring output prefix value of: ", output_prefix)
            print("If you want to use it ensure a year(s) value is provided.")

    else:
        if input_prefix == "":
            print("Using default value for the input prefix: ",
                  " './gpcp_1dd_v1.2_p1d.'")
            input_prefix = "./gpcp_1dd_v1.2_p1d."

        if output_prefix == "":
            print("Using the default output prefix: ./gpcp_out_")
            output_prefix = "./gpcp_out_"

        if input_file != "":
            print("Ignoring output file name of: ", input_file)
            print("If you want to use it ensure a year(s) value ",
                  "is NOT provided.")

        if output_file != "":
            print("Ignoring output file name of: ", output_file)
            print("If you want to use it ensure a year(s) value ",
                  "is NOT provided.")

    return (single_file,
            input_file,
            output_file,
            input_prefix,
            output_prefix,
            months,
            years,
            zipped)

#------------------------------------------------------------------------------
#     Main
#------------------------------------------------------------------------------


def main():
    """ The 'main' function used to run the file/modules as a stand alone
    application.

    """
    the_args = check_args(get_args())

    single_file = the_args[0]
    input_file = the_args[1]
    output_file = the_args[2]
    input_prefix = the_args[3]
    output_prefix = the_args[4]
    months = the_args[5]
    years = the_args[6]
    zipped = the_args[7]

    print("\nStarting process to reformat GPCP binary data to CSV.\n")

    if single_file == True:
        if not output_file.endswith(".csv"):
            output_file = output_file + ".csv"

        files = {input_file: output_file}

    else:  # Process multiple files
        files_dict = {}

        for year in years:
            for month in months:
                if zipped:
                    in_file = input_prefix + year + month + ".gz"
                else:
                    in_file = input_prefix + year + month
                out_file = output_prefix + year + month + ".csv"
                files_dict[in_file] = out_file

        files = files_dict

    for input_file, output_file in sorted(files.iteritems()):
        try:
            if zipped:
                # Extract the zipped file before doing anything else
                z_content = gzip.open(input_file, 'rb')
                with open(input_file[:-3], 'wb') as uncompressed:
                    uncompressed.write(z_content.read())
                input_file = input_file[:-3]

            print("\nExtracting data from ", input_file)
            parser = GpcpParser(input_file)

            if parser.has_data():
                with open(output_file, 'w') as out_file:
                    print("Writing CSV value to ", output_file)
                    parser.write_csv(out_file)

            if zipped:
                os.remove(input_file)

        except IOError:
            print("File: " + output_file + " does NOT exist!  Skipped!")

    print("\nProcess complete.")


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
    # main()
    profile_main()
