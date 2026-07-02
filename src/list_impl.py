# LIST Calc add-in: returns the first or last N rows of a range.
#
# LIST(range; count; include_header)
#   count > 0  -> first  count  rows
#   count < 0  -> last  |count| rows
#   count == 0 -> a single empty cell (or just the header, if requested)
#
# include_header is optional (default 0). When 1 (or TRUE), the first row of
# the range is always returned as a header row, and count then selects from the
# remaining data rows only:
#   LIST(A1:C100; 3; 1)  -> header + first 3 data rows
#   LIST(A1:C100; -5; 1) -> header + last  5 data rows
#
# Registered as the UNO add-in service "com.example.list.ListImpl".

import unohelper

from com.sun.star.sheet import XAddIn
from com.sun.star.lang import XServiceName
from com.example.list import XList

# The add-in service name; must match the AddInInfo node in CalcAddIns.xcu
# and the value returned by getServiceName().
ADDIN_SERVICE = "com.sun.star.sheet.AddIn"
SERVICE_NAME = "com.example.list.ListImpl"
IMPL_NAME = "com.example.list.ListImpl.python"


def _truthy(value):
    """Interpret the optional include_header 'any' from Calc as a bool.

    An omitted argument arrives as None; TRUE()/1 as a number; a text cell as
    a string. A cell reference arrives as a matrix, so fall back to its first
    cell.
    """
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "y", "t")
    try:  # a range/matrix -> look at its top-left cell
        return _truthy(value[0][0])
    except (TypeError, IndexError, KeyError):
        return bool(value)


class ListAddIn(unohelper.Base, XList, XAddIn, XServiceName):
    """Implementation of the LIST spreadsheet function."""

    def __init__(self, ctx):
        self.ctx = ctx
        self._locale = None

    # --- XList ------------------------------------------------------------
    def list(self, data, count, include_header=False):
        # 'data' arrives as a tuple of tuples (rows of column values).
        # 'include_header' arrives as an 'any'; an omitted argument is None.
        if data is None:
            return ((None,),)
        # When a header is requested, peel off the first row and select from
        # the remaining data rows; otherwise keep the original whole-range
        # behaviour untouched.
        if _truthy(include_header):
            header, body = data[:1], data[1:]
        else:
            header, body = (), data
        if count > 0:
            rows = body[:count]
        elif count < 0:
            rows = body[count:]
        else:
            rows = ()
        result = header + rows
        if not result:
            return ((None,),)
        return result

    # --- XAddIn -----------------------------------------------------------
    # Function/argument metadata is supplied by CalcAddIns.xcu, so these
    # return the programmatic names (or empty strings) as a safe fallback.
    def getProgrammaticFuntionName(self, aDisplayName):  # UNO API spelling
        return "list" if aDisplayName == "LIST" else ""

    def getDisplayFunctionName(self, aProgrammaticName):
        return "LIST" if aProgrammaticName == "list" else ""

    def getFunctionDescription(self, aProgrammaticName):
        if aProgrammaticName == "list":
            return "Returns the first or last N rows of a range."
        return ""

    def getDisplayArgumentName(self, aProgrammaticName, nArgument):
        if aProgrammaticName == "list":
            names = ("range", "count", "include_header")
            return names[nArgument] if nArgument in (0, 1, 2) else ""
        return ""

    def getArgumentDescription(self, aProgrammaticName, nArgument):
        if aProgrammaticName == "list":
            if nArgument == 0:
                return "The cell range to list rows from."
            if nArgument == 1:
                return "Number of rows: positive = first N, negative = last N."
            if nArgument == 2:
                return ("Optional. 1 keeps the range's first row as a header; "
                        "count then selects from the data rows only (default 0).")
        return ""

    def getProgrammaticCategoryName(self, aProgrammaticName):
        return "Add-In"

    def getDisplayCategoryName(self, aProgrammaticName):
        return "Add-In"

    # --- XLocalizable (base of XAddIn) ------------------------------------
    def setLocale(self, aLocale):
        self._locale = aLocale

    def getLocale(self):
        return self._locale

    # --- XServiceName -----------------------------------------------------
    def getServiceName(self):
        return SERVICE_NAME


# --- component registration ----------------------------------------------
g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationHelper.addImplementation(
    ListAddIn,
    IMPL_NAME,
    (SERVICE_NAME, ADDIN_SERVICE),
)
