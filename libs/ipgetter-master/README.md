About
=========

This module is designed to fetch your external IP address from the internet.
It is used mostly when behind a NAT.
It picks your IP randomly from a serverlist to minimize request overhead on a single server

If you want to add or remove your server from the list contact me on github


API Usage
=========

    >>> import ipgetter
    >>> myip = ipgetter.myip()
    >>> myip
       '8.8.8.8'

Shell Usage
===========

    $ python -m ipgetter    
    '8.8.8.8'

Installation
============

    # pip install ipgetter

Or download the tarball or git clone the repository and then:

    # python setup.py install

ChangeLog
=========

0.4 (2014-03-01)
 * Serverlist = 44 servers
 * Added timeout for getting the IP

0.3.2 (2014-03-01)
 * Fix distutils issues

0.2 (2014-03-01)
 * Fix python 2 backwards compatibility

0.1 (2014-02-28)
 * You can retrieve your IP.
 * Serverlist = 16 servers
