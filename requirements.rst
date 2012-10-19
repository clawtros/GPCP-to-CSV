Requirements
============

Overview
--------

GPCP binary files needed to be converted to a CSV (Comma Separated Values) 
format for input into a database.  The database format is very specific and 
requires individual lines for each value such as::

>>> date time stamp, latitude, longitude, value

an example would be::

>>> 20110101,45.75,-88.75,0.29

Adam Benzan had written a Python script and placed it on GitHub.  This script
`GPCP-to-CSV <https://github.com/clawtros/GPCP-to-CSV>`_.  provided a 70% 
solution to the requirement above as it converted the binary to 
a CSV format.  However, the CSV format did not meet the specification and 
needed to be completely adjusted.

Examples as Specification
-------------------------

Several original files were provided and are the best specification of the 
the requirements.  The files are linked to below and should be referred to as 
the authority on how to format the output and how the input binary files are 
formatted.

Original Files:

* :download:`Desired Output<./docs/desired_out.txt>`
* :download:`Original Program<./docs/gpcp2csv.py>`

Example Input Files:

* :download:`1987<./docs/gpcp_v2.2_psg.1987>` This is a complete data set.
* :download:`2011<./docs/gpcp_v2.2_psg.2011>` An incomplete data set for testing as incomplete files may be used in production.

Example Output Files:

* :download:`1987<./docs/out1987.csv>`  Output from Mr. Benzan's original program using the input file above.
* :download:`2011<./docs/out2011.csv>`  Output from Mr. Benzan's original program using the incomplete file listed above.

Notes
-----

The first line of the input files is plain text and provides information on
the binary section of the file.  Information such as size, file name, creation
date, variable, units, etc.  One thing not done in the original program was
the extraction and use of this data.

As an aside, a slight tweaking to the appropriate section of the code (such as
adding a header line and breaking the files into months) allows the CSV to be
used in ArcGIS for visualization.  This insight and the fact a new requirement
was placed after the revision was complete (this requirement was to be able
to read and create a CSV from the new GPCP format) prompted the re-write.
This re-write created a parent GpcpParser class with the necessary functions
and two function required to be implemented by all desendents.  Essentially,
this means if a new format is needed for either input or output a programmer
can inheriet from the GpcpParser (or the paraser of choice) and only implement 
the two functions required, write_csv and get_variables. 