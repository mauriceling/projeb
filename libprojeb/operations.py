'''!
Project Entries Binder (ProjEB) Library - Main Operations

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
from modulefinder import ModuleFinder
import os
import random
import subprocess
import sys

from . import utilities

finder = ModuleFinder()

def listDependencies(codefile):
    """!
    Function to list the dependencies (with version number, if any) 
    of the given code file.


    @param codefile String: Path to Python code file.
    @return: List of (dependency name, version, dependency file path).
    """
    filename = os.path.abspath(codefile)
    finder.run_script(codefile)
    results = []
    for name, mod in sorted(finder.modules.items()):
        ver = "No version number"
        if "__version__" in mod.globalnames:
            ver = utilities.load_version_string(mod.__code__)
        modfile = "No file path"
        if mod.__file__ != None:
            modfile = mod.__file__
        results.append((name, str(ver), modfile))
    return results

def listPythonInstalledModules():
    """!
    Function to list the non-standard libraries (with version number, 
    if any) installed in Python.

    @return: List of (module name, version).
    """
    results = subprocess.check_output(["pip", "list", "--format", "freeze"])
    results = results.decode("utf-8")
    results = [x for x in results.split('\r\n') if x != ""]
    results = [x.split('==') for x in results]
    print(results)
    return results