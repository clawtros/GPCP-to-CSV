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

# Built-in/Batteries included Libraries
import cStringIO    # Provides a way write to a memory file and then dump to
                    # the file all at once rather than one line at a time.
                    # This has proven to be faster than using the CSV writer.
import csv
import datetime
import struct

# External Libraries
import mapping


#------------------------------------------------------------------------------
#     Base Class:  GpcpParser
#------------------------------------------------------------------------------


class GpcpParser(object):
    """ The master interface/abstract class should only be inherited from. """
    def __init__(self, filename):
        """ The initialization function for an object. """
        # Ensure data and header variables are reset, critical for looping
        # over a GpcpParser.
        self.data = []
        self.header = ""

        try:
            # Open the file to get the first line of text
            with open(filename, 'r') as get_firstline:
                first_line = get_firstline.readline()

            # Open the file in binary, handle is then used to get the data
            handle = open(filename, 'rb')

        except IOError, error:
            print("\nIOError: ", error)
            print("Skipping file: " + filename + "\n")

        else:
            # Get the variables from the first line of the file
            self.variables = self.get_variables(first_line)
            if self.variables == 0:
                return

            # Read the data from the file given the above variables
            self.header = handle.read(int(self.variables["row_size"]))
            things_per_row = \
                int(self.variables["row_size"]) / \
                int(self.variables["thing_size"])

            # Per the documentation from GPCP in the file structure
            # the floats are -- big-endian --
            # Per python documentation struct uses ">" to determine
            # byte order.  "f" is for float
            row_format = ">" + "f" * things_per_row
            while True:
                packed = handle.read(int(self.variables["row_size"]))
                if packed:
                    row = struct.unpack(row_format, packed)
                    self.data.append(row)
                else:
                    break

            handle.close()

    def has_data(self):
        """ Returns True if there is data in self.data, False otherwise. """
        return len(self.data) > 0

    def generate_map(self):
        """ Generates the needed map and returns it. """
        pstr = self.header[self.header.index('1st_box_center'):]
        start_pstr = mapping.LatLon(*[mapping.Coord(p) \
                         for p in pstr[pstr.index('(') + \
                                       1:pstr.index(')')].split(',')])

        pstr = pstr[pstr.index('2nd_box_center'):]
        next_pstr = mapping.LatLon(*[mapping.Coord(p) \
                        for p in pstr[pstr.index('(') + \
                                      1:pstr.index(')')].split(',')])

        pstr = pstr[pstr.index('last_box_center'):]
        end_pstr = mapping.LatLon(*[mapping.Coord(p) \
                       for p in pstr[pstr.index('(') + \
                                     1:pstr.index(')')].split(',')])

        if self.variables["rows_per_month"] != '':
            rows_per = int(self.variables["rows_per_month"])
        elif self.variables["rows_per_day"] != '':
            rows_per = int(self.variables["rows_per_day"])

        coords = mapping.GeoMap(start_pstr,
                                next_pstr,
                                end_pstr,
                                int(self.variables["points_per_row"]),
                                rows_per)

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
    def get_variables(first_line):
        """ Gets variables from the header. """
        err_str = "This is one of two functions required to implement."
        raise NotImplementedError(err_str)

        return 0

    def write_csv(self, handle):
        """ Writes out the csv data using the cStringIO module.  """
        err_str = "This is one of two functions required to implement."
        raise NotImplementedError(err_str)

#------------------------------------------------------------------------------
#     Class:  GpcpParserOriginal
#------------------------------------------------------------------------------


class GpcpParserOriginal(GpcpParser):
    """ The orginial format map, month of data, month of data, etc. """
    def __init__(self, filename):
        """ The initialization function for an object. """
        GpcpParser.__init__(self, filename=filename)

    def generate_map(self):
        """ overwrite the generate map written for single line entries """
        pstr = self.header[self.header.index('1st_box_center'):]
        start_pt = mapping.LatLon(*[mapping.Coord(p)
                                 for p in pstr[pstr.index('(') + 1:\
                                               pstr.index(')')].split(',')])

        pstr = pstr[pstr.index('2nd_box_center'):]
        next_pt = mapping.LatLon(*[mapping.Coord(p)
                                for p in pstr[pstr.index('(') + 1:\
                                              pstr.index(')')].split(',')])

        pstr = pstr[pstr.index('last_box_center'):]
        end_pt = mapping.LatLon(*[mapping.Coord(p)
                               for p in pstr[pstr.index('(') + 1:\
                                             pstr.index(')')].split(',')])

        return mapping.GeoMap(start_pt, next_pt, end_pt)

    @staticmethod
    def get_variables(first_line):
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
                     "dimensions": "",
                     "1st_box_center": "",
                     "2nd_box_center": "",
                     "last_box_center": ""
                    }

        # Get the values from the first line
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

    def write_csv(self, handle):
        outwriter = csv.writer(handle,
                               delimiter=',',
                               quotechar='|',
                               quoting=csv.QUOTE_MINIMAL)
        coords = self.generate_map()
        outwriter.writerow(["MAP", ])
        for line in coords.map:
            outwriter.writerow(line)

        for idx, row in enumerate(self.data):
            if (idx % int(self.variables["rows_per_month"]) == 0):
                arbitrary_date = datetime.date(2010,
                            idx / int(self.variables["rows_per_month"]) + 1,
                            15)
                outwriter.writerow([arbitrary_date.strftime("%B"), ])

            outwriter.writerow(row)

#------------------------------------------------------------------------------
#     Class:  GpcpParserOriginalOneLine
#------------------------------------------------------------------------------


class GpcpParserOriginalOneLine(GpcpParser):
    """ The orginial file format with one line per data point formatted:
            datetime, lat, lon, value
        and example is:
            19960101,88.75,0.75,0.19

    """
    def __init__(self, filename):
        """ The initialization function for an object. """
        GpcpParser.__init__(self, filename=filename)

    @staticmethod
    def get_variables(first_line):
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
                     "dimensions": "",
                     "1st_box_center": "",
                     "2nd_box_center": "",
                     "last_box_center": ""
                    }

        # Get the values from the first line
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

    def write_csv(self, handle):
        """ Writes out the csv data using the cStringIO module.  """
        # Create a cStingIO object.  Write to the memory 'file' and then
        # in the last line of the function write the entire memory 'file' to
        # disk all at once.
        file_str = cStringIO.StringIO()
        coords = self.generate_map()

        coord_pos = 0
        for idx, row in enumerate(self.data):
            if (idx % int(self.variables['rows_per_month']) == 0):
                arbitrary_date = datetime.date(int(self.variables['year']),
                             idx / int(self.variables['rows_per_month']) + 1,
                             01)
                the_date = (self.variables["year"] + \
                            arbitrary_date.strftime("%m") + \
                            "01")

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
#     Class:  GpcpParserNewOneLine
#------------------------------------------------------------------------------


class GpcpParserNewOneLine(GpcpParser):
    """ The new file format with one line per data point formatted:
            datetime, lat, lon, value
        and example is:
            19960101,88.75,0.75,0.19

    """
    def __init__(self, filename):
        """ The initialization function for an object. """
        GpcpParser.__init__(self, filename=filename)

    @staticmethod
    def get_variables(first_line):
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
