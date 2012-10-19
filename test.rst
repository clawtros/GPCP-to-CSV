Testing and Approval
====================

Overview
--------

Below are files from profile runs.

Run One::

>>> gpcp_to_csv.py -y "1987,2011" -p "../docs/gpcp_v2.2_psg." -f 0

Run Two::

>>> gpcp_to_csv.py -y "1987,2011" -p "../docs/gpcp_v2.2_psg." -f 1

Run Three::

>>> gpcp_to_csv.py -y "1996,2011" -m "6,10" -p "../docs/gpcp_1dd_v1.2_p1d." -f 2 -z 

Also provided is a profile run and pylint output of the completed program.  
The profile log can be used to see where bottle necks.  The pylint output file
is provided to demonstrate the code is clean and meets coding standards. 
Pylint was run using the default configuation and the coding standard follows
PEPs 8 and 257.

Output Files
------------

* :download:`Output for 1987<./docs/gpcp_out_1987.csv>` 
* :download:`Output for 2011<./docs/gpcp_out_2011.csv>`

Pylint
------

* :download:`Pylint Output for gpcp_to_csv.py<./docs/pylint_output_gpcp_to_csv.txt>`
* :download:`Pylint Output for gpcp_parsers.py<./docs/pylint_output_gpcp_parser.txt>`
* :download:`Pylint Output for mapping.py<./docs/pylint_output_mapping.txt>`

Profile
-------

* :download:`Profile Log Run One<./docs/profile_run_one.log>`
* :download:`Profile Log Run Two<./docs/profile_run_two.log>`
* :download:`Profile Log Run Three<./docs/profile_run_three.log>`