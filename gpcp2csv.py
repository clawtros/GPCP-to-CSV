#!/usr/bin/env python
import csv
import sys
import struct 
from datetime import date

ROWSIZE = 576
THINGSIZE = 4
ROWS_PER_MONTH = 72

class Coord:
    def __init__(self, string_representation=None, point=None, direction=None):
        if string_representation:

            direction = string_representation[-1].upper()

            modifier = 1
            if direction in ('S','W'):
                modifier = -1
                direction = 'N' if direction.upper() == 'S' else 'E'

            self.direction = direction
            self.point = modifier * float(string_representation[0:-1])

        elif point and direction:
            self.direction = direction
            self.point = point
        else:
            raise ValueError("must supply string representation or both point and direction")

    def __str__(self):
        return "%f%s" % (self.point, self.direction)

class Lat(Coord):
    def __init__(self, point):
        self.point = point

    def __str__(self):
        return "%0.2f%s" % (self.point if self.point > 0 else (-1*self.point), "N" if self.point > 0 else "S")

class Lon(Coord):
    def __init__(self, point):
        self.point = point

    def __str__(self):
        return "%0.2f%s" % (self.point if self.point > 0 else (-1*self.point), "E" if self.point > 0 else "W")

class LatLng:

    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

    def delta_to(self, other_coord):
        return (abs(self.lat.point - other_coord.lat.point), abs(self.lon.point - other_coord.lon.point))

    def __str__(self):
        return "%s %s" % (str(self.lat), str(self.lon))

class Geomap:
    def __init__(self, topleft, next_point, bottomright, points_per_row=144, rows=72):
        self.map = []
        map_lat = topleft.lat.point
        start_lat = topleft.lat.point
        start_lon = topleft.lon.point

        delta = max(topleft.delta_to(next_point))
        
        for i in range(rows):
            row = []
            map_lon = start_lon
            for j in range(points_per_row):
                row.append(LatLng(Lat(map_lat), Lon(map_lon)))
                map_lon += delta
            self.map.append(row)
            map_lat += -1*delta

    def __str__(self):
        return "\n".join([", ".join([str(ll) for ll in row]) for row in self.map])

class GpcpParser:
    data = []
    header = ""
    
    def __init__(self, filename):
        handle = open(filename, 'rb')
        self.header = handle.read(ROWSIZE)
        things_per_row = ROWSIZE/THINGSIZE
        format = ">" + "f" * things_per_row

        while True:
            packed = handle.read(ROWSIZE)
            if packed:
                row = struct.unpack(format, packed)
                self.data.append(row) 
            else:
                break

    def generate_map(self):
        pstr = self.header[self.header.index('1st_box_center'):]
        start = LatLng(*[Coord(p) for p in pstr[pstr.index('(')+1:pstr.index(')')].split(',')])

        pstr = pstr[pstr.index('2nd_box_center'):]
        next = LatLng(*[Coord(p) for p in pstr[pstr.index('(')+1:pstr.index(')')].split(',')])

        pstr = pstr[pstr.index('last_box_center'):]
        end = LatLng(*[Coord(p) for p in pstr[pstr.index('(')+1:pstr.index(')')].split(',')])

        return Geomap(start, next, end)

    def has_data(self):
        return len(self.data) > 0

    def write_csv(self, handle):
        outwriter = csv.writer(handle, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
        coords = self.generate_map()
        outwriter.writerow(["MAP",])
        for line in coords.map:
            outwriter.writerow(line)

        for idx, row in enumerate(self.data):
                
            if (idx % ROWS_PER_MONTH == 0):
                arbitrary_date = date(2010, idx / ROWS_PER_MONTH + 1, 15)
                outwriter.writerow([arbitrary_date.strftime("%B"),])

            outwriter.writerow(row)
            
if __name__ == "__main__":
    filename = None
    outfile = None
    try:
        filename = sys.argv[1]
    except IndexError, e:
        filename = "gpcp_v2.1_psg.2009"

    try:
        outfile = sys.argv[2]
    except IndexError, e:
        outfile = "out.csv"

    parser = GpcpParser(filename)

    if parser.has_data():
        outhandle = open(outfile, 'w')
        parser.write_csv(outhandle)
        outhandle.close()
