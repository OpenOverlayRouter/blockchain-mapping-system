from distutils.core import setup


def get_version(relpath):
    """read version info from file without importing it"""
    from os.path import dirname, join
    for line in open(join(dirname(__file__), relpath)):
        if '__version__' in line:
            if '"' in line:
                # __version__ = "0.1"
                return line.split('"')[1]
            elif "'" in line:
                return line.split("'")[1]
            
setup(
    name='ipgetter',
    version=get_version('ipgetter.py'),
    author='Fernando Giannasi <phoemur@gmail.com>',
    url='https://github.com/phoemur/ipgetter',
    download_url = 'https://github.com/phoemur/ipgetter/tarball/0.4',

    description="Utility to fetch your external IP address",
    license="Public Domain",
    classifiers=[
        'Environment :: Console',
        'License :: Public Domain',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking',
        'Topic :: Utilities',
    ],

    py_modules=['ipgetter'],

    long_description='''This module is designed to fetch your external IP address from the internet. It is used mostly when behind a NAT. It picks your IP 
randomly from a serverlist to minimize request overhead on a single server

If you want to add or remove your server from the list contact me on github''',
)
