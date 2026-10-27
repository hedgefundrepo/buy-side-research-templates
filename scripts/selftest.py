#!/usr/bin/env python3
"""Zero-cost self-test for the kit: no network, no model calls, standard library only.

    python3 scripts/selftest.py          # run from the kit (or repo) root

Checks:
  1. risk_factor_diff.py on the two fictional ExampleCo fixtures finds exactly what was planted
     (2 added, 2 removed, 2 changed, 1 certainty shift, 1 moved heading) and skips the table of contents.
  2. Every .xlsx under spreadsheets/ is a valid workbook package, carries the disclaimer on every sheet,
     contains no cached spreadsheet error values, and has no personal author in its properties.
  3. Every template under templates/ carries the disclaimer.
Exit code 0 only if every check passes.
"""
import pathlib, re, sys, zipfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import risk_factor_diff as rfd  # noqa: E402

DISCLAIMER = "Educational only. Not investment advice. Independent; not affiliated with any fund or firm."
BRAND = "The Hedge Fund&apos;s Repository|The Hedge Fund's Repository"
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + name + (f"  ({detail})" if detail and not ok else ""))


# 1. diff script on fixtures
fx = HERE / "fixtures"
res, scope = rfd.run(fx / "exampleco-10k-fy2024.htm", fx / "exampleco-10k-fy2025.htm")
check("diff: Item 1A located (table of contents skipped)", scope == "Item 1A", scope)
check("diff: 2 added blocks", len(res["added"]) == 2, len(res["added"]))
check("diff: 2 removed blocks", len(res["removed"]) == 2, len(res["removed"]))
check("diff: 2 changed paragraphs", len(res["changed"]) == 2, len(res["changed"]))
check("diff: 1 certainty shift (could -> have reduced)",
      len(res["certainty_shifts"]) == 1 and "have reduced" in res["certainty_shifts"][0]["new"], res["certainty_shifts"])
check("diff: largest-customer heading moved up", len(res["moved_headings"]) == 1
      and res["moved_headings"][0]["heading"].startswith("Our largest customer"), res["moved_headings"])
check("diff: tariff risk detected as added", any("tariffs" in a for a in res["added"]))
check("diff: covenant risk detected as removed", any("covenants" in r for r in res["removed"]))
check("diff: page furniture ignored", not any(re.fullmatch(r"(Page \d+|Table of Contents)", x)
                                              for x in res["added"] + res["removed"]))
whole, scope2 = rfd.run(fx / "exampleco-10k-fy2024.htm", fx / "exampleco-10k-fy2025.htm", whole=True)
check("diff: --whole mode runs", scope2 == "whole document" and len(whole["added"]) >= 2)

# 2. spreadsheets
ERR = re.compile(r"<v>#(REF!|DIV/0!|NAME\?|VALUE!|N/A|NUM!|NULL!)</v>")
books = sorted((ROOT / "spreadsheets").glob("*.xlsx"))
check("xlsx: workbooks present", len(books) >= 1, "none found")
for b in books:
    try:
        z = zipfile.ZipFile(b)
        sheets = [n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n)]
        shared = z.read("xl/sharedStrings.xml").decode("utf-8") if "xl/sharedStrings.xml" in z.namelist() else ""
        missing = [s for s in sheets if DISCLAIMER not in z.read(s).decode("utf-8") and DISCLAIMER not in shared]
        check(f"xlsx: {b.name} opens as a package with {len(sheets)} sheets", len(sheets) > 0)
        check(f"xlsx: {b.name} disclaimer on every sheet", not missing, missing)
        check(f"xlsx: {b.name} no cached error values",
              not any(ERR.search(z.read(s).decode("utf-8")) for s in sheets))
        core = z.read("docProps/core.xml").decode("utf-8")
        creators = re.findall(r"<dc:creator[^>]*>(.*?)</dc:creator>|<cp:lastModifiedBy>(.*?)</cp:lastModifiedBy>", core)
        names = {x for pair in creators for x in pair if x}
        check(f"xlsx: {b.name} author is the brand only", names <= set(BRAND.split("|")), names)
    except (zipfile.BadZipFile, KeyError) as e:
        check(f"xlsx: {b.name} readable", False, e)

# 3. templates
for t in sorted((ROOT / "templates").glob("*.md")):
    check(f"template: {t.name} carries the disclaimer", DISCLAIMER in t.read_text(encoding="utf-8"))

passed = sum(results)
print(f"\nselftest: {passed}/{len(results)} passed")
sys.exit(0 if passed == len(results) else 1)
