
**build** Configuration Module
==============================

Overview
--------
Byte-compiles all supporting python files/modules for use in the production
environment.  On the production environment the $PYTHON_DIR location is not
writable by the users and thus the need to byte-compile the files as they
are being deployed.

Notes for Deployment
~~~~~~~~~~~~~~~~~~~~
* ALWAYS run dos2unix on the files after they are moved to $PYTHON_DIR.  This
  last baseline push this was a gotcha as the files when viewed in both more 
  and vi did not show any ^M at the end of lines like a normal dos files does.  
  We used this to indicate there was a problem but the lack of ^M endings lead
  us to look elsewhere for the problem. 

* ALWAYS run the build.py file as /usr/local/bin/python2.6 build.py as this 
  sets the Python environment for other users.

Description
-----------
.. automodule:: build
	:members: