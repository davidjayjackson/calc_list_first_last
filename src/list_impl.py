# LIST Calc add-in: returns the first or last N rows of a range.
#
# LIST(range; count)
#   count > 0  -> first  count  rows
#   count < 0  -> last  |count| rows
#   count == 0 -> a single empty cell
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


class ListAddIn(unohelper.Base, XList, XAddIn, XServiceName):
    """Implementation of the LIST spreadsheet function."""

    def __init__(self, ctx):
        self.ctx = ctx
        self._locale = None

    # --- XList ------------------------------------------------------------
    def list(self, data, count):
        # 'data' arrives as a tuple of tuples (rows of column values).
        if data is None:
            return ((None,),)
        if count > 0:
            rows = data[:count]
        elif count < 0:
            rows = data[count:]
        else:
            return ((None,),)
        if not rows:
            return ((None,),)
        return rows

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
            return ("range", "count")[nArgument] if nArgument in (0, 1) else ""
        return ""

    def getArgumentDescription(self, aProgrammaticName, nArgument):
        if aProgrammaticName == "list":
            if nArgument == 0:
                return "The cell range to list rows from."
            if nArgument == 1:
                return "Number of rows: positive = first N, negative = last N."
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
