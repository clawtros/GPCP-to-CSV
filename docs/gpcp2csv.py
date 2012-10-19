#!/usr/local/bin/python2.6
"""
Purpose
-------
    Takes an input binary file of a well know format, extracts the data and
    saves it in a simple but required CSV foramt.

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

"""
#------------------------------------------------------------------------------
#     Imports
#------------------------------------------------------------------------------


import cProfile
import csv
import datetime
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
    """ For printing a coordinate, i.e. a latitude and longitude of
        a point.

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


class Lat(Coord):
    def __init__(self, point):
        self.point = point

    def __str__(self):
        return "%0.2f%s" % \
               (self.point \
                if self.point > 0 \
                else (-1 * self.point), "N" if self.point > 0 else "S")

class Lon(Coord):
    def __init__(self, point):
        self.point = point

    def __str__(self):
        return "%0.2f%s" % \
               (self.point \
                if self.point > 0 \
                else (-1 * self.point), "E" if self.point > 0 else "W")

class LatLon(object):

    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

    def delta_to(self, other_coord):
        return (abs(self.lat.point - other_coord.lat.point),
                abs(self.lon.point - other_coord.lon.point))

    def __str__(self):
        return "%s %s" % (str(self.lat), str(self.lon))

#------------------------------------------------------------------------------
#     Class:  GeoMap
#------------------------------------------------------------------------------


class GeoMap(object):
    """ Defines a map area and associated string for printing. """
    def __init__(self,
                 topleft,
                 next_point,
                 bottomright,
                 points_per_row,
                 rows):
        """ The initialization function """
        self.map = []
        map_lat = topleft.lat.point
        _start_lat = topleft.lat.point
        start_lon = topleft.lon.point

        delta = max(topleft.delta_to(next_point))

        for _i in range(rows):
            row = []
            map_lon = start_lon
            for _j in range(points_per_row):
                row.append(LatLon(Lat(map_lat), Lon(map_lon)))
                map_lon += delta
            self.map.append(row)
            map_lat += -1 * delta

    def __str__(self):
        """ For printing the instance of the object. """
        return "\n".join([", ".join([str(ll) for ll in row]) \
                          for row in self.map])

#------------------------------------------------------------------------------
#     Class:  GpcpParser
#------------------------------------------------------------------------------


class GpcpParser(object):
    """ Takes an input file name and then writes output to a CSV. """
    data = []
    header = ""

    def __init__(self, filename):
        """ The initialization function for an object. """
        # Get the variables from the first line of the file
        self.variables = self.get_variables(filename)

        handle = open(filename, 'rb')
        self.header = handle.read(int(self.variables["row_size"]))
        things_per_row = \
            int(self.variables["row_size"]) / int(self.variables["thing_size"])

        # Per documentation for file structure the floats are big-endian
        # struct uses ">" to determine byte order.  "f" is for float
        row_format = ">" + "f" * things_per_row

        while True:
            packed = handle.read(int(self.variables["row_size"]))
            if packed:
                row = struct.unpack(row_format, packed)
                self.data.append(row)
            else:
                break

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
                        int(self.variables["rows_per_month"]))

        coords_map = []
        for line in coords.map:
            for coord in line:
                latitude, longitude = str(coord).split(" ")
                if latitude[-1] == "S":
                    latitude = float("-" + latitude[:-1])
                else:
                    latitude = float(latitude[:-1])

                longitude = float(longitude[:-1]) - 180

                coords_map.append([latitude, longitude])

        return coords_map

    def get_variables(self, inputfile):
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
                "months": "",
                "start_month": "",
                "end_month": "",
                "rows_per_month": "",
                "grid": "",
                "dimensions": ""
                }

        # Open the file, inputfile, and read only the first line
        with open(inputfile, "r") as the_input:
            first_line = the_input.readline()

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
        variables["start_month"], variables["end_month"] = \
            variables["months"].split("-")
        variables["rows_per_month"] = variables["dimensions"].split("x")[2]

        return variables

    def has_data(self):
        """ Returns True if there is data in self.data, False otherwise. """
        return len(self.data) > 0

    def write_csv(self, handle):
        """ Writes out the csv data using the csv module.  """
        out_writer = csv.writer(handle,
                               delimiter=',',
                               quotechar='|',
                               quoting=csv.QUOTE_MINIMAL)
        coords = self.generate_map()

        for coord in coords:
            line_out = [self.variables["year"],
                        coord[0],
                        coord[1]]
            out_writer.writerow(line_out)
            # out_writer.writerow(line)

        for idx, row in enumerate(self.data):
            if (idx % int(self.variables['rows_per_month']) == 0):
                arbitrary_date = datetime.date(2010,
                             idx / int(self.variables['rows_per_month']) + 1,
                             15)
                out_writer.writerow([self.variables["year"] + \
                                     arbitrary_date.strftime("%m") + \
                                     "01", ])

            out_writer.writerow(row)

#------------------------------------------------------------------------------
#     Main
#------------------------------------------------------------------------------


def main():
    """ The 'main' function used to run the file/modules as a stand alone
    application

    """
    filename = None
    outfile = None
    try:
        filename = sys.argv[1]
    except IndexError, error:
        filename = "../docs/gpcp_v2.2_psg.2011"
        print "Input File Index Error: ", error

    try:
        outfile = sys.argv[2]
    except IndexError, error:
        outfile = "out.csv"
        print "Output File Index Error: ", error

    parser = GpcpParser(filename)

    if parser.has_data():
        outhandle = open(outfile, 'w')
        parser.write_csv(outhandle)
        outhandle.close()


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
    stats.print_stats(80)  # 80 = how many to print
    # The rest is optional.
    # stats.print_callees()
    # stats.print_callers()
    logging.info("Profile data:\n%s", stream.getvalue())


def test_main():
    """ For running unit tests """
    pass

#------------------------------------------------------------------------------
#     Name
#------------------------------------------------------------------------------


if __name__ == '__main__':
    main()
    # profile_main()
    # test_main()
