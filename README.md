# buy-side-research-templates

Free, tested templates for a professional equity-research **process**: an idea pipeline spreadsheet, a 10-K checklist keyed to the filing's own items, a thesis one-pager with kill triggers, a pre-mortem, and a small script that diffs the risk factors between two annual reports.

> **Educational only. Not investment advice. Independent; not affiliated with any fund or firm.**
> These are process tools. Every example company is fictional (ExampleCo). Nothing here recommends a security or a strategy.

## What's inside

| Path | What it does |
|---|---|
| `spreadsheets/Idea-Pipeline.xlsx` | Five-stage idea pipeline (inbox, triage, first read, deep work, decision) with triage scoring, days in stage, a deep-work cap, drop reasons, and a source hit-rate table. Classic functions only (tested in Excel and LibreOffice; every function used also exists in Google Sheets). |
| `templates/10-K-Checklist.md` | 25 questions keyed to Form 10-K items (1, 1A, 1C, 3, 7, 7A, 8, 9A, Part III, exhibits), scored green / amber / red. |
| `templates/Thesis-One-Pager.md` | A thesis in five sentences, plus pillars with observable KPIs and kill triggers decided in advance. |
| `templates/Pre-Mortem.md` | "It is two years from now and this failed." Thirty minutes, before deciding. |
| `scripts/risk_factor_diff.py` | Compares Item 1A (Risk Factors) between two saved filings, paragraph by paragraph: added, removed, changed (word-level diff), "could" to "has" certainty shifts, and headings that moved up. Python 3.8+, standard library only, no network. |
| `scripts/selftest.py` | Zero-cost self-test on two fictional filings, plus checks on every workbook and template. |
| `.claude/skills/risk-factor-diff/` | The same diff as a Claude Code skill: `/risk-factor-diff older.htm newer.htm`. |

## Use

```bash
git clone https://github.com/hedgefundrepo/buy-side-research-templates
cd buy-side-research-templates
python3 scripts/selftest.py                                   # expect: selftest: N/N passed
python3 scripts/risk_factor_diff.py older-10k.htm newer-10k.htm -o diff.md
```

On Windows use `python` instead of `python3`. To get the inputs, open the company's filing index on EDGAR, download the primary `.htm` document of two consecutive 10-Ks, and pass both paths.

## Why diff risk factors?

Risk factors are mostly boilerplate, which is why the *changes* carry signal: a new risk, a deleted one, or a sentence that moved from "could adversely affect" to "has adversely affected". Generic text-compare tools drown that in page headers and reflowed lines. This script extracts Item 1A, normalizes it, and compares paragraph to paragraph.

## Want the rest?

This repo is a free subset of **The Analyst's Research Kit** (my own product): a three-statement model skeleton with a balance check and cash tie-out, an earnings scorecard, a thesis tracker that flags OK / WATCH / KILL, 10 templates, and three Claude Code skills. It implements the 20 plays in **The Buy-Side Research Playbook**.

- Free 5-play sampler (by email): https://hedgefundrepo.substack.com/subscribe
- The Playbook, $29: https://hedgefundrepo.gumroad.com/l/playbook
- The Kit, $49: https://hedgefundrepo.gumroad.com/l/kit

## Licence

Code (`scripts/`, `.claude/`) is MIT (see `LICENSE`). Templates and spreadsheets are CC BY 4.0 (see `LICENSE-TEMPLATES.md`): use and adapt them freely, with attribution to "The Hedge Fund's Repository".

*Educational only. Not investment advice. Independent; not affiliated with any fund or firm.*
