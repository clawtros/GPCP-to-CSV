Analysis and Design
===================

Overview
--------

The simplest design is for a command line program. The program will provide
a help feature explaining its options.  Once the command line program is built 
it would be relatively easy to add an input dialog GUI interface on top of it.  
This last step will occur as time permits.  The changes to the original program
are described below.

Command Line Inputs
-------------------

An example use of the program would be::

> python gpcp2csv.py -h

This could also be entered as::

> gpcp2csv.py --help

and provides all the options such as below::

    usage: gpcp_to_csv.py [-h] [-z] [-s] [-i INPUT_FILE] [-o OUTPUT_FILE]
                      [-p INPUT_PREFIX] [-op OUTPUT_PREFIX] [-y YEARS]
                      [-m MONTHS] [-f FORMAT]

	Please see http://precip.gsfc.nasa.gov/ for a full description of the data
	set.

	optional arguments:
	  -h, --help            show this help message and exit
	  -z, --gzip            Set this flag if the input files are zipped using gzip
							and end with .gz.
	  -s, --single_file     Set this flag if running the program for only a single
							(one) file. Specify the file using the -i option.
	  -i INPUT_FILE, --input_file INPUT_FILE
							The full path of the input file, i.e.:
							C:/Users/schiefej/Desktop/gpcp_v2.2psg.1987 if no
							year(s) is(are) provided this is required. If this
							switch is used, -s must also be set.
	  -o OUTPUT_FILE, --output_file OUTPUT_FILE
							The full path of the input file, i.e.:
							C:/Users/schiefej/Desktop/out_1987.csv
	  -p INPUT_PREFIX, --input_prefix INPUT_PREFIX
							The path to the input file(s) and the appropriate
							prefix such as: './gpcp_v2.2_psg.' or
							'C:/Users/schiefej/binary_files/gpcp_file_'The default
							is the current directory plus the prefix for the new
							format files: './gpcp_1dd_v1.2_p1d.'
	  -op OUTPUT_PREFIX, --output_prefix OUTPUT_PREFIX
							The path to the output file(s) and the appropriate
							prefix such as: './gpcp_out_' or
							'C:/Users/schiefej/binary_files/gpcp_out_'
	  -y YEARS, --years YEARS
							Years of the requested data, i.e. 2012 or 1987,2011.
							The MUST be no spaces in the string, ie. 1999,2000 is
							okay but 1999, 2000 is not.This is a optional value
							but if it is provided, prefixes must be provided. If
							it is provided, an input file must be provided.
	  -m MONTHS, --months MONTHS
							Months of the requested data, i.e. 10 or
							1,2,3,4,5,6,7,8,9,10,11,12 for an entire year. There
							MUST be no spaces in the string; see the year argument
							for applicable examples but using month numbers.
	  -f FORMAT, --format FORMAT
							This switch determines which parser to use. 0 decodes
							MONTHLY GPCP (v2.2) binary file into CSV output. Tags
							the data by month and pre-pends a list of grid box
							lat/lons in the same order as the precip data itself.
							Format originally designed by Adler, et al.1 decodes
							MONTHLY GPCP (v2.2) binary data into CSV with a
							date/lat/lon value for each precip value in the file.
							One line per value. 2 decodes DAILY GPCP (v1.2) binary
							file into same csv format as 1 above.

	Special thanks to clawtros/Adam Benzan and Carbon Chick for their initial
	program that solved the hard problem.


Users of Unix/Linux environments will find the above familiar and
easy to follow.

Changes to Original Script
--------------------------

Added the get_variables() function.  The dictionary returned by this function
is used then to determine file dimensions, date and other bits of information
needed in the remainder of the class.

"... premature optimization is the root of all evil." -- Donald Knuth

Given this I took some time to try some optimizations to get some practical
experience.  The only significant improvement to be made once a profiler was
run was to use available memory and only write to the file once.  This is 
where the cStringIO.StringIO() function is used and was admittedly only a 
marginal optimization at best but it was perceptible and was left in the code.
If the data set increase in size significantly this may become problematic 
depending on the memory of the machine.  For now it is a good trade off and 
readability of the code did not suffer.

The place for formatting the code is in the GpcpParser.write_csv function.
This single function controls how the output is formatted.  As stated in the 
"Notes" in Requirements, deriving from GpcpParser and then writing separate 
functions each format is one way of solving this problem.   
