"""End-to-end test for the LIST Calc add-in.

Run with LibreOffice's bundled Python (it ships the `uno` module) against a
headless instance listening on a UNO socket:

    soffice --headless --norestore --accept="socket,host=localhost,port=2002;urp;"
    "C:\\Program Files\\LibreOffice\\program\\python.exe" tools\\test_list.py

Prints RESULT: PASS / FAIL and exits non-zero on failure.
"""
import sys
import time
import uno


def connect(port=2002, tries=40):
    local = uno.getComponentContext()
    resolver = local.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local)
    url = "uno:socket,host=localhost,port=%d;urp;StarOffice.ComponentContext" % port
    last = None
    for _ in range(tries):
        try:
            return resolver.resolve(url)
        except Exception as e:  # not yet listening
            last = e
            time.sleep(0.5)
    raise SystemExit("could not connect to LibreOffice: %s" % last)


def main():
    ctx = connect()
    smgr = ctx.ServiceManager
    desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
    doc = desktop.loadComponentFromURL("private:factory/scalc", "_blank", 0, ())
    try:
        sheet = doc.Sheets.getByIndex(0)
        data = [["a", 1, 10], ["b", 2, 20], ["c", 3, 30],
                ["d", 4, 40], ["e", 5, 50], ["f", 6, 60]]
        sheet.getCellRangeByName("A1:C6").setDataArray(
            tuple(tuple(r) for r in data))

        # count > 0 -> first N rows
        sheet.getCellRangeByName("E1:G3").setArrayFormula("=LIST(A1:C6;3)")
        first = sheet.getCellRangeByName("E1:G3").getDataArray()

        # count < 0 -> last |N| rows
        sheet.getCellRangeByName("E5:G6").setArrayFormula("=LIST(A1:C6;-2)")
        last = sheet.getCellRangeByName("E5:G6").getDataArray()

        # include_header 1 -> header row + last |N| data rows
        sheet.getCellRangeByName("E8:G10").setArrayFormula(
            "=LIST(A1:C6;-2;1)")
        last_hdr = sheet.getCellRangeByName("E8:G10").getDataArray()
    finally:
        doc.close(False)
        desktop.terminate()

    def norm(rows):
        return tuple(tuple(float(x) if isinstance(x, int) else x for x in row)
                     for row in rows)

    exp_first, exp_last = norm(data[:3]), norm(data[-2:])
    # header (row 0) + last 2 data rows (rows 1..)
    exp_last_hdr = norm([data[0]] + data[-2:])
    ok_first, ok_last = first == exp_first, last == exp_last
    ok_last_hdr = last_hdr == exp_last_hdr

    print("first 3 rows:", first)
    print("last 2 rows :", last)
    print("hdr+last 2  :", last_hdr)
    print("MATCH_FIRST     :", ok_first)
    print("MATCH_LAST      :", ok_last)
    print("MATCH_LAST_HDR  :", ok_last_hdr)
    ok = ok_first and ok_last and ok_last_hdr
    print("RESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
