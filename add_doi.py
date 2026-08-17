# -*- coding: utf-8 -*-
"""add_doi.py — insert the Zenodo DOI into CITATION.cff and README.

Usage:  python add_doi.py 10.5281/zenodo.1234567

Run from the repo root after Zenodo mints the DOI. Edits both files,
validates the CITATION.cff, and prints what to commit.
"""
import sys, os, re

if len(sys.argv) != 2:
    print(__doc__)
    raise SystemExit(1)

doi = sys.argv[1].strip().replace("https://doi.org/", "")
if not re.match(r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$", doi):
    print("Not a DOI:", doi)
    raise SystemExit(1)

root = os.path.dirname(os.path.abspath(__file__))

# --- CITATION.cff: uncomment the identifiers block and fill the value
p = os.path.join(root, "CITATION.cff")
t = open(p, encoding="utf-8").read()
t = t.replace(
    "# identifiers:            # uncomment after the first Zenodo release\n"
    "#   - type: doi\n"
    "#     value: 10.5281/zenodo.0000000\n"
    "#     description: Concept DOI resolving to the latest version.",
    "identifiers:\n"
    "  - type: doi\n"
    "    value: %s\n"
    "    description: Concept DOI resolving to the latest version." % doi)
if "doi:" not in t.split("identifiers:")[0]:
    t = t.replace("type: dataset", "type: dataset\ndoi: %s" % doi, 1)
open(p, "w", encoding="utf-8", newline="\n").write(t)

# --- README: badge under the title, DOI line in the citation block
p = os.path.join(root, "README.md")
r = open(p, encoding="utf-8").read()
# citation block first: the badge also contains "doi.org", so inserting it
# first would make a naive guard skip this edit.
old_cite = ("Awoyemi, A. (2026). LUMA WNBA Stint and Lineup Data (Version 1.0.0) [Data set].\n"
            "https://github.com/lumahoops/WNBA")
if old_cite in r:
    r = r.replace(old_cite,
                  "Awoyemi, A. (2026). LUMA WNBA Stint and Lineup Data (Version 1.0.0) [Data set].\n"
                  "Zenodo. https://doi.org/%s" % doi, 1)
badge = "[![DOI](https://zenodo.org/badge/DOI/%s.svg)](https://doi.org/%s)" % (doi, doi)
if "zenodo.org/badge" not in r:
    r = r.replace("# LUMA WNBA Stint and Lineup Data\n", "# LUMA WNBA Stint and Lineup Data\n\n%s\n" % badge, 1)
open(p, "w", encoding="utf-8", newline="\n").write(r)

try:
    import yaml
    d = yaml.safe_load(open(os.path.join(root, "CITATION.cff"), encoding="utf-8"))
    print("CITATION.cff valid, %d fields" % len(d))
    print("  doi:", d.get("doi"))
    print("  identifiers:", d.get("identifiers"))
except ImportError:
    print("pyyaml not installed; skipped validation")

print("\nDOI inserted:", doi)
print("\nNext:")
print("  git add -A")
print('  git commit -m "Add Zenodo DOI"')
print("  git push")
