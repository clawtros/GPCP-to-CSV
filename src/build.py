#!/usr/local/bin/python2.6
"""
Purpose
-------
    To pre-compile all the python files and modules needed for the
    project baseline in production.  As this area lacks write capability
    by all but one user on the baseline the ability to create pyc
    (pre-compile python byte code) is limited and must be done when
    the baseline is deployed.  This "script" takes care of this
    functionality.

Program Flow
------------
    Takes the directory the file is in and pre-compiles all files
    with a .py extension.

    Input:
        A file with a .py extension.

    Output:
        Compiled python byte code for the interpreter on the server
        used for running production code.

Notes
-----
    The page http://effbot.org/zone/python-compile.htm is a good place
    for a general discussion of the tools used to build python projects.

"""

#------------------------------------------------------------------------------
#     Imports
#------------------------------------------------------------------------------


import compileall

#------------------------------------------------------------------------------
#     Functions
#------------------------------------------------------------------------------


def main():
    """
    Runs the program, stand alone, from the command line.

    """
    print "\n  Building current Project Python Baseline ...\n\n"
    compileall.compile_dir("./", force=True)
    print "\n\n  The Project Python Baseline is built. \n\n"

#------------------------------------------------------------------------------
#     Main
#------------------------------------------------------------------------------


if __name__ == "__main__":
    main()
