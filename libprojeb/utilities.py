'''!
Project Entries Binder (ProjEB) Utilities

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

import dis

def load_version_string(codeobj):
    """!
    Returns the constant value loaded for the `__version__` global

    Requires that `__version__` is set from a literal constant value.
    """
    instructions = dis.get_instructions(codeobj)
    for instr in instructions:
        if instr.opname == 'LOAD_CONST':
            nxtop = next(instructions, None)
            if nxtop.opname == 'STORE_NAME' and \
                nxtop.argval == '__version__':
                return instr.argval