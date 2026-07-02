# "List rows" macro for the LIST Calc add-in.
#
# Invoked from the LIST menu / toolbar button installed by the extension.
# It auto-detects the contiguous data block around the current selection,
# asks for a row count and an output cell, then writes the first or last N
# rows there (a manual "spill", since LibreOffice functions cannot spill).
#
#   count > 0  -> first  count  rows
#   count < 0  -> last  |count| rows
#
# apply_rows() is a headless-friendly entry point used by the test harness.

from com.sun.star.awt.MessageBoxType import INFOBOX, ERRORBOX
from com.sun.star.awt.MessageBoxButtons import BUTTONS_OK

_BTN_OK = 1      # com.sun.star.awt.PushButtonType.OK
_BTN_CANCEL = 2  # com.sun.star.awt.PushButtonType.CANCEL


# --- helpers --------------------------------------------------------------
def _col_name(idx):
    """0-based column index -> spreadsheet column letters (0 -> A)."""
    name = ""
    idx += 1
    while idx:
        idx, rem = divmod(idx - 1, 26)
        name = chr(65 + rem) + name
    return name


def _range_name(addr):
    """CellRangeAddress -> 'A1:C6' (sheet-local)."""
    return "%s%d:%s%d" % (
        _col_name(addr.StartColumn), addr.StartRow + 1,
        _col_name(addr.EndColumn), addr.EndRow + 1)


def _write(doc, source_name, count, target_name, include_header=False):
    """Write the first/last `count` rows of source_name into target_name.

    When include_header is true, the source's first row is always written as a
    header and `count` selects from the remaining data rows only.

    Returns (rows_written, cols_written).
    """
    sheet = doc.getCurrentController().getActiveSheet()
    data = sheet.getCellRangeByName(source_name).getDataArray()
    if include_header:
        header, body = data[:1], data[1:]
    else:
        header, body = (), data
    if count >= 0:
        rows = body[:count]
    else:
        rows = body[count:]
    rows = header + rows
    if not rows:
        return (0, 0)
    nrows, ncols = len(rows), len(rows[0])
    addr = sheet.getCellRangeByName(target_name).getRangeAddress()
    c0, r0 = addr.StartColumn, addr.StartRow
    out = sheet.getCellRangeByPosition(c0, r0, c0 + ncols - 1, r0 + nrows - 1)
    out.setDataArray(rows)
    return (nrows, ncols)


def _msgbox(ctx, doc, message, title, kind=INFOBOX):
    smgr = ctx.getServiceManager()
    toolkit = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
    parent = doc.getCurrentController().getFrame().getContainerWindow()
    box = toolkit.createMessageBox(parent, kind, BUTTONS_OK, title, message)
    box.execute()
    box.dispose()


def _ask(ctx, default_count, default_target):
    """Modal dialog for count + output cell + header flag.

    Returns (count, target, include_header) or None.
    """
    smgr = ctx.getServiceManager()
    model = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialogModel", ctx)
    model.Width, model.Height, model.Title = 190, 112, "List rows"

    def add(name, kind, **props):
        ctrl = model.createInstance("com.sun.star.awt.UnoControl%sModel" % kind)
        for key, val in props.items():
            setattr(ctrl, key, val)
        model.insertByName(name, ctrl)

    add("lblCount", "FixedText", PositionX=6, PositionY=9, Width=86, Height=12,
        Label="Number of rows:")
    add("edCount", "Edit", PositionX=96, PositionY=6, Width=86, Height=14,
        Text=default_count)
    add("lblCell", "FixedText", PositionX=6, PositionY=31, Width=86, Height=12,
        Label="Output top-left cell:")
    add("edCell", "Edit", PositionX=96, PositionY=28, Width=86, Height=14,
        Text=default_target)
    add("chkHeader", "CheckBox", PositionX=6, PositionY=51, Width=178,
        Height=12, Label="Include header row (range's first row)", State=0)
    add("lblHint", "FixedText", PositionX=6, PositionY=67, Width=178,
        Height=20, Label="Positive = first N rows, negative = last N rows.")
    add("btnOk", "Button", PositionX=74, PositionY=92, Width=52, Height=14,
        Label="OK", PushButtonType=_BTN_OK, DefaultButton=True)
    add("btnCancel", "Button", PositionX=130, PositionY=92, Width=52,
        Height=14, Label="Cancel", PushButtonType=_BTN_CANCEL)

    dialog = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialog", ctx)
    dialog.setModel(model)
    toolkit = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
    dialog.createPeer(toolkit, None)
    ok = dialog.execute()
    count_text = dialog.getControl("edCount").getModel().Text.strip()
    cell_text = dialog.getControl("edCell").getModel().Text.strip()
    include_header = dialog.getControl("chkHeader").getModel().State == 1
    dialog.dispose()
    if ok != _BTN_OK:
        return None
    try:
        count = int(count_text)
    except ValueError:
        return None
    if not cell_text:
        return None
    return (count, cell_text, include_header)


# --- entry points ---------------------------------------------------------
def list_rows(*args):
    """Menu/toolbar entry point (shows dialogs)."""
    ctx = XSCRIPTCONTEXT.getComponentContext()  # noqa: F821 (injected)
    doc = XSCRIPTCONTEXT.getDocument()           # noqa: F821 (injected)
    try:
        if not doc.supportsService("com.sun.star.sheet.SpreadsheetDocument"):
            _msgbox(ctx, doc, "Please run this inside a Calc spreadsheet.",
                    "List rows", ERRORBOX)
            return
        controller = doc.getCurrentController()
        sheet = controller.getActiveSheet()
        selection = controller.getSelection()
        if selection is None or not hasattr(selection, "getRangeAddress"):
            _msgbox(ctx, doc, "Select a cell inside your data first.",
                    "List rows", ERRORBOX)
            return
        anchor = selection.getRangeAddress()
        cursor = sheet.createCursorByRange(
            sheet.getCellByPosition(anchor.StartColumn, anchor.StartRow))
        cursor.collapseToCurrentRegion()
        src = cursor.getRangeAddress()
        source_name = _range_name(src)
        default_target = "%s%d" % (_col_name(src.EndColumn + 2), src.StartRow + 1)

        answer = _ask(ctx, "10", default_target)
        if answer is None:
            return
        count, target_name, include_header = answer
        nrows, _ = _write(doc, source_name, count, target_name, include_header)
        if nrows == 0:
            _msgbox(ctx, doc, "Nothing to list (count was 0 or range empty).",
                    "List rows")
    except Exception as exc:  # surface any failure to the user
        _msgbox(ctx, doc, "Error: %s" % exc, "List rows", ERRORBOX)


def apply_rows(source_name, count, target_name, include_header=0):
    """Headless entry point for tests: no dialogs. Returns 'OK:RxC'."""
    doc = XSCRIPTCONTEXT.getDocument()  # noqa: F821 (injected)
    nrows, ncols = _write(doc, source_name, int(count), target_name,
                          bool(int(include_header)))
    return "OK:%dx%d" % (nrows, ncols)


g_exportedScripts = (list_rows, apply_rows)
