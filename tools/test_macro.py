"""End-to-end test for the "List rows" macro command.

Runs against a headless LibreOffice with the extension installed, using
LibreOffice's bundled Python:

    soffice --headless --norestore --accept="socket,host=localhost,port=2002;urp;"
    "C:\\Program Files\\LibreOffice\\program\\python.exe" tools\\test_macro.py

It verifies both that the menu/toolbar script URL resolves (so the button
dispatches) and that the writer produces the right first/last rows.
"""
import sys
import time
import uno

BASE = "vnd.sun.star.script:LIST.oxt|Scripts|python|list_rows.py$%s"
SUFFIX = "?language=Python&location=user:uno_packages"
MENU_URI = BASE % "list_rows" + SUFFIX
APPLY_URI = BASE % "apply_rows" + SUFFIX


def connect(port=2002, tries=60):
    local = uno.getComponentContext()
    resolver = local.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local)
    url = "uno:socket,host=localhost,port=%d;urp;StarOffice.ComponentContext" % port
    for _ in range(tries):
        try:
            return resolver.resolve(url)
        except Exception:
            time.sleep(0.5)
    raise SystemExit("could not connect to LibreOffice")


def main():
    ctx = connect()
    smgr = ctx.ServiceManager
    desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
    doc = desktop.loadComponentFromURL("private:factory/scalc", "_blank", 0, ())
    # make the doc "current" so the macro's XSCRIPTCONTEXT.getDocument() finds it
    doc.getCurrentController().getFrame().activate()
    try:
        sheet = doc.Sheets.getByIndex(0)
        data = [["a", 1, 10], ["b", 2, 20], ["c", 3, 30],
                ["d", 4, 40], ["e", 5, 50], ["f", 6, 60]]
        sheet.getCellRangeByName("A1:C6").setDataArray(
            tuple(tuple(r) for r in data))

        factory = smgr.createInstanceWithContext(
            "com.sun.star.script.provider.MasterScriptProviderFactory", ctx)
        provider = factory.createScriptProvider(doc)

        # 1. the button URL must resolve
        provider.getScript(MENU_URI)

        # 2. functional check via the headless entry point
        apply = provider.getScript(APPLY_URI)
        apply.invoke(("A1:C6", 3, "E1"), (), ())
        apply.invoke(("A1:C6", -2, "E5"), (), ())
        # include_header=1 -> header row + last 2 data rows
        apply.invoke(("A1:C6", -2, "E8", 1), (), ())
        first = sheet.getCellRangeByName("E1:G3").getDataArray()
        last = sheet.getCellRangeByName("E5:G6").getDataArray()
        last_hdr = sheet.getCellRangeByName("E8:G10").getDataArray()
    finally:
        doc.close(False)
        desktop.terminate()

    def norm(rows):
        return tuple(tuple(float(x) if isinstance(x, int) else x for x in r)
                     for r in rows)

    ok = (first == norm(data[:3]) and last == norm(data[-2:])
          and last_hdr == norm([data[0]] + data[-2:]))
    print("first 3 rows:", first)
    print("last 2 rows :", last)
    print("hdr+last 2  :", last_hdr)
    print("RESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
