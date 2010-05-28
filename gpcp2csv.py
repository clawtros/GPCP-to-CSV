#!/usr/bin/env python
import csv
import sys
import struct 
from datetime import date

ROWSIZE = 576
THINGSIZE = 4
ROWS_PER_MONTH = 72

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
        start_lon, start_lat = pstr[pstr.index('(')+1:pstr.index(')')].split(',')
        pstr = pstr[pstr.index('last_box_center'):]
        end_lon, end_lat = pstr[pstr.index('(')+1:pstr.index(')')].split(',')
        return (start_lon, start_lat, end_lon, end_lat)

    def has_data(self):
        return len(self.data) > 0

    def write_csv(self, handle):
        outwriter = csv.writer(handle, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
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
