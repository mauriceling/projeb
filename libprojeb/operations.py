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

def listPythonSystem():
    """!
    Function to list information about the installed Python system.

    @return: Dictionary of {attributes: values}.
    """
    try: dllhandle = sys.dllhandle
    except AttributeError: dllhandle = "Not Defined"
    try: androidapilevel = sys.getandroidapilevel()
    except AttributeError: androidapilevel = "Not Defined"
    try: dlopenflags = sys.getdlopenflags()
    except AttributeError: dlopenflags = "Not Defined"
    try: windowsversion_major = sys.getwindowsversion().major 
    except AttributeError: windowsversion_major = "Not Defined"
    try: windowsversion_minor = sys.getwindowsversion().minor 
    except AttributeError: windowsversion_minor = "Not Defined"
    try: windowsversion_build = sys.getwindowsversion().build 
    except AttributeError: windowsversion_build = "Not Defined"
    try: windowsversion_platform = sys.getwindowsversion().platform
    except AttributeError: windowsversion_platform = "Not Defined"
    try: 
        service_pack = sys.getwindowsversion().service_pack
        if service_pack == '': 
            service_pack = 'Not Specified'
    except AttributeError: service_pack = "Not Defined"
    try: winver = sys.winver
    except AttributeError: winver = "Not Defined"
    if sys.thread_info.lock == None:
        thread_info_lock = "Not Defined"
    else:
        thread_info_lock = sys.thread_info.lock
    if sys.thread_info.version == None:
        thread_info_version = "Not Defined"
    else:
        thread_info_version = sys.thread_info.version
    results = {"allocatedblocks": str(sys.getallocatedblocks()),
               "androidapilevel": str(androidapilevel),
               "api_version": str(sys.api_version),
               "base_exec_prefix": str(sys.base_exec_prefix),
               "base_prefix": str(sys.base_prefix),
               "byteorder": str(sys.byteorder),
               "builtin_module_names": ' | '.join(sys.builtin_module_names),
               "defaultencoding": str(sys.getdefaultencoding()),
               "dllhandle": str(dllhandle),
               "dlopenflags": str(dlopenflags),
               "exec_prefix": str(sys.exec_prefix),
               "executable": str(sys.executable),
               "filesystemencoding": str(sys.getfilesystemencoding()),
               "filesystemencodeerrors": str(sys.getfilesystemencodeerrors()),
               "flag_debug": str(sys.flags.debug),
               "flag_inspect": str(sys.flags.inspect), 
               "flag_interactive": str(sys.flags.interactive), 
               "flag_optimize": str(sys.flags.optimize), 
               "flag_dont_write_bytecode": str(sys.flags.dont_write_bytecode), 
               "flag_no_user_site": str(sys.flags.no_user_site), 
               "flag_no_site": str(sys.flags.no_site), 
               "flag_ignore_environment": str(sys.flags.ignore_environment), 
               "flag_verbose": str(sys.flags.verbose), 
               "flag_bytes_warning": str(sys.flags.bytes_warning), 
               "flag_quiet": str(sys.flags.quiet), 
               "flag_has_randomization": str(sys.flags.hash_randomization), 
               "flag_isolated": str(sys.flags.isolated), 
               "flag_dev_mode": str(sys.flags.dev_mode), 
               "flag_utf8_mode": str(sys.flags.utf8_mode),
               "float_info_max": str(sys.float_info.max), 
               "float_info_max_exp": str(sys.float_info.max_exp), 
               "float_info_max_10_exp": str(sys.float_info.max_10_exp), 
               "float_info_min": str(sys.float_info.min), 
               "float_info_min_exp": str(sys.float_info.min_exp), 
               "float_info_min_10_exp": str(sys.float_info.min_10_exp), 
               "float_info_dig": str(sys.float_info.dig), 
               "float_info_mant_dig": str(sys.float_info.mant_dig), 
               "float_info_epsilon": str(sys.float_info.epsilon), 
               "float_info_radix": str(sys.float_info.radix), 
               "float_info_rounds": str(sys.float_info.rounds),
               "float_repr_style": str(sys.float_repr_style),
               "hash_info_width": str(sys.hash_info.width), 
               "hash_info_modulus": str(sys.hash_info.modulus), 
               "hash_info_inf": str(sys.hash_info.inf), 
               "hash_info_nan": str(sys.hash_info.nan), 
               "hash_info_imag": str(sys.hash_info.imag), 
               "hash_info_algorithm": str(sys.hash_info.algorithm), 
               "hash_info_hash_bits": str(sys.hash_info.hash_bits), 
               "hash_info_seed_bits": str(sys.hash_info.seed_bits), 
               "hash_info_cutoff": str(sys.hash_info.cutoff),
               "hexversion": str(sys.hexversion),
               "implementation_name": str(sys.implementation.name),
               "implementation_cache_tag": str(sys.implementation.cache_tag),
               "int_info_bits_per_digit": str(sys.int_info.bits_per_digit), 
               "int_info_sizeof_digit": str(sys.int_info.sizeof_digit),
               "maxsize": str(sys.maxsize),
               "maxunicode": str(sys.maxunicode),
               "platform": str(sys.platform),
               "prefix": str(sys.prefix),
               "recursionlimit": str(sys.getrecursionlimit()),
               "switchinterval": str(sys.getswitchinterval()),
               "thread_info_name": str(sys.thread_info.name),
               "thread_info_lock": str(thread_info_lock),
               "thread_info_version": str(thread_info_version),
               "version_info_major": str(sys.version_info.major), 
               "version_info_minor:": str(sys.version_info.minor), 
               "version_info_micro": str(sys.version_info.micro), 
               "version_info_releaselevel": str(sys.version_info.releaselevel), 
               "version_info_serial": str(sys.version_info.serial),
               "windowsversion_major": str(windowsversion_major),
               "windowsversion_minor": str(windowsversion_minor),
               "windowsversion_build": str(windowsversion_build), 
               "windowsversion_platform": str(windowsversion_platform),
               "windowsversion_service_pack": str(service_pack),               
               "winver": str(sys.winver)}
    return results
