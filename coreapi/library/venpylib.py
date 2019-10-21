"""
Created on Mon Oct 12 22:50:41 2015

@author: Patrick Breach
@email: <pbreach@uwo.ca>
"""
import ctypes
from ctypes import util
import platform
import re
from itertools import product
from collections import OrderedDict

import numpy as np
import pandas as pd


def load(model, dll='vendll64.dll'):
    """Load compiled Vensim model using the Vensim DLL.

    Parameters
    ----------
    model : str
        compiled (.vpm) Vensim model filepath
    dll : str, default 'vendll32.dll'
        name of installed Vensim dll file

    Returns
    -------
    VenPy model object
    """
    return VenPy(model, dll)


class VenPy(object):

    def __init__(self, model, dll):
        # Get bitness and OS
        bit, opsys = platform.architecture()

        # Filter numbers out of string
        def nums(X): return "".join(x for x in X if str.isdigit(x))

        # Assert same bitness of Python and Vensim
        assert nums(dll) == nums(bit), \
            "%s version of Python will not work with %s" % (bit, dll)

        # Get path to Vensim dll
        path = util.find_library(dll)

        # Make sure OS is Windows
        if "Windows" not in opsys:
            raise OSError("Not supported for %s" % opsys)
        # Test if path was obtained for Vensim dll
        elif not path:
            raise IOError("Could not find Vensim DLL '%s'" % dll)

        # Load Vensim dll
        try:
            self.dll = ctypes.windll.LoadLibrary(path)
        except Exception as e:
            print(e)
            print("'%s' could not be loaded using the path '%s'" % (dll, path))

        # Load compiled vensim model
        self.cmd("SPECIAL>LOADMODEL|%s" % model)

        # Get all variable names from model based on type
        types = {1: 'level', 2: 'aux', 3: 'data', 4: 'init', 5: 'constant',
                 6: 'lookup', 7: 'group', 8: 'sub_range', 9: 'constraint',
                 10: 'test_input', 11: 'time_base', 12: 'game',
                 13: 'sub_constant'}

        self.vtype = {}

        for num, var in types.items():
            maxn = self.dll.vensim_get_varnames(b'*', num, None, 0)
            names = (ctypes.c_char * maxn)()
            self.dll.vensim_get_varnames(b'*', num, names, maxn)
            names = _c_char_to_list(names)

            for n in names:
                if n:
                    self.vtype[n.encode('ISO-8859-1').decode('utf-8')] = var

        # Set empty components dictionary
        self.components = OrderedDict()
        # Set runname as none when no simulation has taken place
        self.runname = None

    def __getitem__(self, key):

        # Test for subcript type of string
        if self._is_subbed(key):
            # Get subscript element information
            var, elements, combos = self._get_sub_info(key)

            if all(len(e) == 1 for e in elements):
                return self._getval(key)

            else:
                # Get shape of resulting array
                shape = [len(e) for e in elements]
                # Get values of subscript combinations
                values = [self._getval(c) for c in combos]

                return np.array(values).reshape(shape).squeeze()

        else:
            return self._getval(key)

    def __setitem__(self, key, val):

        if isinstance(val, (int, float)):
            # Setting single int or float
            self._setval(key, val)

        elif hasattr(val, "__call__"):
            # Store callable as model component called when run
            self.components[key] = val

        elif (type(val) == np.ndarray or type(val) == list) and self._is_subbed(key):
            # Get subscript element information
            var, elements, combos = self._get_sub_info(key)

            if all(len(e) == 1 for e in elements):
                TypeError("Array or list cannot be set to fully subscripted "
                          "variable %s" % key)

            else:
                # Convert values to strings and flatten out array
                values = np.array(val).flatten().astype(str)
                # Make sure correct number of elements are being set
                assert len(values) == len(combos), "Array has %s elements, " \
                                                   "while '%s' has %s elements" % (
                                                       len(values), key, len(combos))
                # Set subscript combinations
                for c, v in zip(combos, values):
                    self._setval(c, v)

        else:

            message = "Unsupported type '%s' passed to __setitem__ for Venim" \
                      "variable '%s'." % (type(val), key)
            raise TypeError(message)

    def run(self, runname='Run', interval=1):
        """
        Run the loaded Vensim model.

        Parameters
        ----------
        runname : str, default 'Run'
            Label for model results. Use a different name for distinguishing
            output between multiple runs.
        interval : int, default 1
            The number of time steps defining the interval for which the
            control of the simulation is returned to the user defined functions
            (if any). Communication occurs at the beginning of each interval.
        """
        # Do not display any messages from Vensim
        self.dll.vensim_be_quiet(1)
        # Set simulation name before running
        self.runname = runname
        self.cmd("SIMULATE>RUNNAME|%s" % runname)

        # Run entire simulation if no components are set
        if not self.components:
            self.cmd("MENU>RUN|O")
        else:
            # Run simulation step by step
            initial = self.__getitem__("INITIAL TIME")
            final = self.__getitem__("FINAL TIME")
            dt = self.__getitem__("TIME STEP")

            if (initial - final) % interval:
                msg = "total time steps are not evenly divisible by interval."
                raise ValueError(msg)
            elif interval < dt:
                raise ValueError("Interval should be greater than time step.")

            # Start the simulation
            self.cmd("MENU>GAME|O")
            self.cmd("GAME>GAMEINTERVAL|%s" % interval)

            step = interval if interval else dt

            # Run user defined function(s) at every step
            for t in np.arange(initial, final, step):
                self._run_udfs()
                self.cmd("GAME>GAMEON")

            self.cmd("GAME>ENDGAME")

    def cmd(self, cmd):
        """Send a command using the Vensim DLL.

        Parameters
        ----------
        cmd : str
            Valid string command for Vensim DLL
        """
        success = self.dll.vensim_command(_prepstr(cmd))
        if not success:
            raise Exception("Vensim command '%s' was not successful." % cmd)

    def v_encode(self):
        mtype = {}
        for n, v in self.vtype.items():
            mtype[n.encode('utf-8').decode('ISO-8859-1')] = v
        self.vtype = mtype

    def v_decode(self):
        mtype = {}
        for n, v in self.vtype.items():
            mtype[n.encode('ISO-8859-1').decode('utf-8')] = v
        self.vtype = mtype

    def result(self, names=None, vtype=None):
        """Get last model run results loaded into python. Specific variables
        can be retrieved using the `names` attribute, or all variables of a
        specific type can be returned using the `vtype` attribute.

        All variables of type 'level', 'aux', and 'game' are returned by
        default.

        Parameters
        ----------
        names : str or sequence, default None
            Variable names for which the data will be retrieved. By default,
            all model levels and auxiliarys are returned. If an iterable is
            passed, a subset of these will be returned.
        vtype : str, default None
            Return result for variable names of specific types(s). Valid types
            that can be specified are 'level', 'aux', and/or 'game'.

        Returns
        -------
        result : dict
             Python dictionary will be returned where the keys are Vensim model
             names and values are lists corresponding to model output for each
             timstep.
        """
        self.v_encode()

        if names:
            names = [name.encode('utf-8').decode('ISO-8859-1')
                     for name in names]
        # Make sure results are generated before retrieved
        assert self.runname, "Run before results can be obtained."
        # Make sure both kwargs are not set simultaneously
        assert not (names and vtype), "Only one of either 'names' or 'vtype'" \
                                      " can be set."

        valid = set(['level', 'aux', 'game'])

        if names:
            # Make sure all names specified are in the model
            assert all(n in self.vtype.keys() for n in names), "One or more " \
                                                               "names are not defined in Vensim."
            # Ensure specified names are of the appropriate type
            types = set([self.vtype[n] for n in names])
            assert valid >= types, "One or more names are not of type " \
                                   "'level', 'aux', or 'game'."
            varnames = names

        elif vtype:
            # Make sure vtype is valid
            assert vtype in valid, "'vtype' must be 'level', 'aux', or 'game'."
            varnames = [n for n, v in self.vtype.items() if v == vtype]

        else:
            varnames = [n for n, v in self.vtype.items() if v in valid]

        if not varnames:
            raise Exception("No variables of specified type(s).")

        allvars = []
        for v in varnames:
            if self._is_subbed(v):
                allvars += [v + s for s in self._get_sub_elements([v])[0]]
            else:
                allvars.append(v)

        result = {}

        for v in allvars:

            maxn = self.dll.vensim_get_data(_prepstr(self.runname), _prepstr(v),
                                            b'Time', None, None, 0)

            vval = (ctypes.c_float * maxn)()
            tval = (ctypes.c_float * maxn)()

            success = self.dll.vensim_get_data(_prepstr(self.runname),
                                               _prepstr(v),
                                               b'Time', vval, tval, maxn)

            if not success:
                raise IOError("Could not retrieve data for '%s'"
                              " corresponding to run '%s'" % (v, self.runname))

            result[v.encode('ISO-8859-1').decode('utf-8')] = np.array(vval)
        self.v_decode()
        return pd.DataFrame(result, index=np.array(tval))

    def _run_udfs(self):
        for key in self.components:
            # Ensure only gaming type variables can be set during sim
            if self._is_subbed(key):
                name, _ = self._get_subs(key)
            else:
                name = key

            assert self.vtype[name] == 'game', \
                "%s must be of 'Gaming' type to set during sim." % key
            # Set vensim variable using component function output
            val = self.components[key]()
            self.__setitem__(key, val)

    def _getval(self, key):
        # Define ctypes single precision floating point number
        result = ctypes.c_float()
        # Store value based on key lookup in result
        success = self.dll.vensim_get_val(_prepstr(key), ctypes.byref(result))

        if not success:
            raise KeyError("Unable to query value for '%s'." % key)
        elif result.value == -1.298074214633707e33:
            vtype = self.vtype[key]
            raise KeyError("Cannot get '%s' outside simulation." % vtype)

        return result.value

    def _setval(self, key, val):
        # Set the value of a Vensim variable
        cmd = "SIMULATE>SETVAL|%s=%s" % (key, val)
        self.cmd(cmd)

    def _get_sub_info(self, key):
        var, subs = self._get_subs(key)
        elements = self._get_sub_elements(subs)
        combos = [var + "[%s]" % ','.join(c) for c in product(*elements)]
        return var, elements, combos

    def _get_sub_elements(self, subs):
        elements = []
        for s in subs:
            if self.vtype[s] != 'sub_constant':
                maxn = self.dll.vensim_get_varattrib(_prepstr(s), 9, None, 0)
                res = (ctypes.c_char * maxn)()
                self.dll.vensim_get_varattrib(_prepstr(s), 9, res, maxn)
                elements.append(_c_char_to_list(res))
            else:
                elements.append([s])
        return elements

    def _is_subbed(self, key):
        maxn = self.dll.vensim_get_varattrib(_prepstr(key), 9, None, 0)
        return False if maxn == 2 else True

    def _get_subs(self, key):
        names = [str.strip(i) for i in re.findall(r'[^\[|^\]|^,]+', key)]
        return names[0], names[1:]


def _c_char_to_list(res):
    names = []
    for r in list(res)[:-2]:
        if isinstance(r, str):
            names.append(r)
        else:
            names.append(r.decode('ISO-8859-1'))
    names = ''.join(names).split('\x00')

    return names


def _prepstr(in_str):
    return in_str if isinstance(in_str, bytes) else in_str.encode('ISO-8859-1')
