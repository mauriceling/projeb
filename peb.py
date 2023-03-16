'''!
Project Entries Binder (ProjEB) Command Line Interface (CLI)

Date created: 28th April 2019

License: GNU General Public License version 3 for academic or 
not-for-profit use only


ProjEB is free software: you can redistribute it and/or modify it 
under the terms of the GNU General Public License as published by the 
Free Software Foundation, either version 3 of the License, or (at 
your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
'''
import argparse
import os
import random
import subprocess
import sys

import libprojeb


def listDependencies(codefile):
    """!
    Function to list the dependencies (with version number, if any) 
    of the given code file.

    Usage:

        python peb.py listdep --codefile=<path to Python code file>

    Results are shown in the following format:

        <count> : <dependency name> : <version> : <dependency file path>

    @param codefile String: Path to Python code file.
    """
    codefile = os.path.abspath(codefile)
    results = libprojeb.listDependencies(codefile)
    print("Count : Dependency Name : Version : Dependency File Path")
    count = 1
    for x in results:
        print("%s : %s : %s : %s" % (str(count), x[0], x[1], x[2]))
        count = count + 1

def listPythonInstalledModules():
    """!
    Function to list the non-standard libraries (with version number, 
    if any) installed in Python.

    Usage:

        python peb.py listpim

    Results are shown in the following format:

        <count> : <module name> : <version>
    """
    results = libprojeb.listPythonInstalledModules()
    print("Count : Module Name : Version")
    count = 1
    for x in results:
        print("%s : %s : %s" % (str(count), x[0], x[1]))
        count = count + 1

def listPythonSystem():
    """!
    Function to list information about the installed Python system.

    Usage:

        python peb.py listpysys

    Results are shown in the following format:

        <count> : <attribute name> : <attribute value>
    """
    results = libprojeb.listPythonSystem()
    print("Count : Attribute : Value")
    count = 1
    for x in results:
        print("%s : %s : %s" % (str(count), x, results[x]))
        count = count + 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest="command")

    listdep = subparser.add_parser("listdep")
    listdep.add_argument('--codefile', type=str, required=True, help="path of file to check for dependencies")
    
    listpim = subparser.add_parser("listpim")
    
    listpysys = subparser.add_parser("listpysys")
    
    args = parser.parse_args()

    if args.command.lower() == "listdep": listDependencies(os.path.abspath(args.codefile))
    elif args.command.lower() == "listpim": listPythonInstalledModules()
    elif args.command.lower() == "listpysys": listPythonSystem()
