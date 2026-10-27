#!/usr/bin/env python3
"""Compare Item 1A (Risk Factors) between two annual reports, paragraph by paragraph.

    python3 risk_factor_diff.py OLD.htm NEW.htm                 # markdown report to stdout
    python3 risk_factor_diff.py OLD.htm NEW.htm -o report.md    # write to a file
    python3 risk_factor_diff.py OLD.txt NEW.txt --json          # machine-readable output
    python3 risk_factor_diff.py OLD.htm NEW.htm --whole         # skip Item 1A detection, diff everything

Inputs are filings you saved yourself (the .htm primary document from EDGAR, or plain text). The script
never touches the network. Standard library only; Python 3.8+.

What it reports:
  - ADDED, REMOVED and CHANGED paragraphs (changed = matched by similarity, shown as a word-level diff)
  - CERTAINTY shifts: a matched paragraph that moved from "could/may/might" language to "has/have/had"
  - MOVED headings: a risk heading that climbed 3+ places in the order

Educational only. Not investment advice. Independent; not affiliated with any fund or firm.
"""
import argparse, difflib, html, json, re, sys
from html.parser import HTMLParser

BLOCK_TAGS = {"p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6", "table", "section", "td"}
START_RE = re.compile(r"item\s*1a\s*[.:\-–—]?\s*risk\s+factors", re.I)
END_RE = re.compile(r"item\s*1b\s*[.:\-–—]?\s*unresolved|item\s*1c\s*[.:\-–—]?\s*cybersecurity"
                    r"|item\s*2\s*[.:\-–—]?\s*properties", re.I)
FURNITURE_RE = re.compile(r"^(table of contents|page \d+|\d{1,3}|[ivxlc]{1,6})$", re.I)
HEDGE_RE = re.compile(r"\b(could|may|might|would)\b", re.I)
FACT_RE = re.compile(r"\b(has|have|had|did|were|was)\b\s+(\w+ed|been|experienced|identified|incurred|received)", re.I)
SIMILARITY = 0.6


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        elif tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip = max(0, self.skip - 1)
        elif tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def to_text(raw):
    if re.search(r"<(html|body|p|div|span|table)\b", raw[:20000], re.I):
        p = _Text(); p.feed(raw); raw = "".join(p.parts)
    return html.unescape(raw).replace(" ", " ")


def section(text, whole=False):
    """Return the Item 1A body. Picks the longest start->end span, which skips the table of contents."""
    if whole:
        return text, "whole document"
    best = None
    for m in START_RE.finditer(text):
        e = END_RE.search(text, m.end())
        end = e.start() if e else len(text)
        if best is None or end - m.end() > best[1] - best[0]:
            best = (m.end(), end)
    if not best or best[1] - best[0] < 200:
        return text, "Item 1A not found; diffed whole document"
    return text[best[0]:best[1]], "Item 1A"


def blocks(text):
    out = []
    for line in text.split("\n"):
        line = re.sub(r"\s+", " ", line).strip()
        if not line or FURNITURE_RE.match(line):
            continue
        heading = len(line) < 160 and not line.endswith((".", ";", ":")) and len(line.split()) <= 22
        out.append({"text": line, "heading": heading})
    return out


def norm(s):
    return re.sub(r"[^a-z0-9 ]", "", s.lower())


def word_diff(a, b):
    aw, bw = a.split(), b.split()
    res = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, aw, bw, autojunk=False).get_opcodes():
        if op == "equal":
            res.append(" ".join(aw[i1:i2]))
        if op in ("delete", "replace"):
            res.append("[-" + " ".join(aw[i1:i2]) + "-]")
        if op in ("insert", "replace"):
            res.append("{+" + " ".join(bw[j1:j2]) + "+}")
    return " ".join(res)


def compare(old_blocks, new_blocks):
    old_n = [norm(b["text"]) for b in old_blocks]
    new_n = [norm(b["text"]) for b in new_blocks]
    used_old, pairs = set(), {}
    index = {}
    for i, n in enumerate(old_n):
        index.setdefault(n, []).append(i)
    for j, n in enumerate(new_n):                       # pass 1: exact matches
        for i in index.get(n, []):
            if i not in used_old:
                used_old.add(i); pairs[j] = (i, 1.0); break
    for j, n in enumerate(new_n):                       # pass 2: best similar paragraph
        if j in pairs or new_blocks[j]["heading"]:
            continue
        best, best_r = None, 0.0
        for i, o in enumerate(old_n):
            if i in used_old or old_blocks[i]["heading"]:
                continue
            sm = difflib.SequenceMatcher(None, o, n, autojunk=False)
            if sm.real_quick_ratio() < SIMILARITY or sm.quick_ratio() < SIMILARITY:
                continue
            r = sm.ratio()
            if r > best_r:
                best, best_r = i, r
        if best is not None and best_r >= SIMILARITY:
            used_old.add(best); pairs[j] = (best, best_r)

    added = [new_blocks[j]["text"] for j in range(len(new_blocks)) if j not in pairs]
    removed = [old_blocks[i]["text"] for i in range(len(old_blocks)) if i not in used_old]
    changed, certainty = [], []
    for j, (i, r) in sorted(pairs.items()):
        if r < 1.0:
            a, b = old_blocks[i]["text"], new_blocks[j]["text"]
            item = {"similarity": round(r, 2), "old": a, "new": b, "diff": word_diff(a, b)}
            changed.append(item)
            if HEDGE_RE.search(a) and FACT_RE.search(b) and not FACT_RE.search(a):
                certainty.append(item)
    # heading order moves
    old_h = [norm(b["text"]) for b in old_blocks if b["heading"]]
    new_h = [(norm(b["text"]), b["text"]) for b in new_blocks if b["heading"]]
    moved = []
    for rank_new, (n, txt) in enumerate(new_h):
        if n in old_h:
            delta = old_h.index(n) - rank_new
            if delta >= 3:
                moved.append({"heading": txt, "from": old_h.index(n) + 1, "to": rank_new + 1})
    unchanged = sum(1 for _, r in pairs.values() if r == 1.0)
    return {"added": added, "removed": removed, "changed": changed, "certainty_shifts": certainty,
            "moved_headings": moved, "unchanged": unchanged}


def report(res, old_name, new_name, scope):
    L = [f"# Risk-factor diff: {old_name} -> {new_name}", "",
         f"Scope: {scope}. Unchanged blocks: {res['unchanged']}. "
         f"Added: {len(res['added'])}. Removed: {len(res['removed'])}. Changed: {len(res['changed'])}. "
         f"Certainty shifts: {len(res['certainty_shifts'])}. Moved headings: {len(res['moved_headings'])}.", ""]
    def sec(title, items, fmt):
        L.append(f"## {title} ({len(items)})"); L.append("")
        L.extend(fmt(x) for x in items) if items else L.append("_none_")
        L.append("")
    sec("Certainty shifts (could/may -> has/had)", res["certainty_shifts"], lambda x: f"- {x['diff']}")
    sec("Added", res["added"], lambda x: f"- {x}")
    sec("Removed", res["removed"], lambda x: f"- {x}")
    sec("Changed", res["changed"], lambda x: f"- ({x['similarity']}) {x['diff']}")
    sec("Moved headings", res["moved_headings"], lambda x: f"- {x['heading']}: position {x['from']} -> {x['to']}")
    L.append("For each added or changed paragraph, ask: what event or fact explains this change, and is it in "
             "the MD&A, an 8-K, or the news? (Playbook, Play 5)")
    L.append("")
    L.append("_Educational only. Not investment advice. Independent; not affiliated with any fund or firm._")
    return "\n".join(L)


def run(old_path, new_path, whole=False):
    texts = []
    scopes = []
    for p in (old_path, new_path):
        with open(p, encoding="utf-8", errors="replace") as f:
            body, scope = section(to_text(f.read()), whole)
        texts.append(blocks(body)); scopes.append(scope)
    scope = scopes[0] if scopes[0] == scopes[1] else f"old: {scopes[0]}; new: {scopes[1]}"
    return compare(*texts), scope


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("old"); ap.add_argument("new")
    ap.add_argument("-o", "--out"); ap.add_argument("--json", action="store_true")
    ap.add_argument("--whole", action="store_true", help="diff the whole document, not just Item 1A")
    a = ap.parse_args(argv)
    res, scope = run(a.old, a.new, a.whole)
    out = json.dumps(dict(res, scope=scope), indent=2) if a.json else report(res, a.old, a.new, scope)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(out + "\n")
        print(f"wrote {a.out}")
    else:
        sys.stdout.write(out + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
