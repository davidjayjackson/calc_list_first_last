# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Optional `include_header` argument to `LIST`.** `LIST(range; count;
  include_header)` — when `include_header` is `1`, the range's first row is
  always returned as a header and `count` selects from the remaining data rows
  only. Defaults to `0`; `TRUE()`/`FALSE()` are also accepted.
- **"Include header row" checkbox** in the "List rows" dialog, applying the
  same header behavior to the menu/toolbar command.

## [1.0.0] - 2026-07-02

First release of **LIST**, a LibreOffice Calc extension for listing the first or
last *N* rows of a range.

### Added
- **`LIST(range; count)` worksheet function.** Signed count: a positive `count`
  returns the first N rows, a negative `count` returns the last N. Enter as an
  array formula with **Ctrl+Shift+Enter**. Appears in the Function Wizard under
  the **Add-In** category.
- **"List rows" menu and toolbar command.** Auto-detects the contiguous data
  block around the current selection, prompts for a row count and output cell,
  and writes the first/last N rows into the sheet (a practical "spill"). No
  whole-column penalty and no Ctrl+Shift+Enter required.
- UNO type library (`XList` IDL), Python add-in component, and Python macro,
  packaged as an installable `.oxt` extension via `build.ps1`.
- Headless end-to-end tests (`tools/test_list.py`, `tools/test_macro.py`).
- Logos and screenshots under `assets/`.
- README documenting usage, range-syntax rules, build/install, and packaging
  notes.

[Unreleased]: https://github.com/davidjayjackson/calc_list_first_last/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/davidjayjackson/calc_list_first_last/releases/tag/v1.0.0
