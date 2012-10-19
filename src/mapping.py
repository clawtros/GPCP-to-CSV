#!/usr/local/bin/python2.6
"""
Purpose
-------
    Provides the ability to create Lat/Lon and Coord data structs for
    creating points for a mapping of the GPCP binary data sets.

Program Flow
------------
    See each class for a full description of what and how it does.


Notes/Lessons Learned
---------------------
    TODO: Create testing frame work for this set of classes.

--------

"""
#------------------------------------------------------------------------------
#     Imports
#------------------------------------------------------------------------------


# No imports are needed for this set of classes.

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

#------------------------------------------------------------------------------
#     Class:  Lat
#------------------------------------------------------------------------------


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

#------------------------------------------------------------------------------
#     Class:  Lon
#------------------------------------------------------------------------------


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

#------------------------------------------------------------------------------
#     Class:  LatLon
#------------------------------------------------------------------------------


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
                 points_per_row=144,
                 rows=72):
        """ The initialization function.  The default values for
        points_per_row and rows are provided for the original format.

        """
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
