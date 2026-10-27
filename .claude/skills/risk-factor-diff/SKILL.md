---
name: risk-factor-diff
description: Compare Item 1A (Risk Factors) between two saved annual reports paragraph by paragraph, then turn every added, removed or changed risk into a research question. Use when the user has two 10-K files (or 10-Q risk-factor sections) and asks what changed in the risk factors.
argument-hint: "<older-filing.htm> <newer-filing.htm>"
allowed-tools: Read, Bash(python3 "${CLAUDE_SKILL_DIR}/risk_factor_diff.py" *), Bash(python "${CLAUDE_SKILL_DIR}/risk_factor_diff.py" *), Bash(python3 ${CLAUDE_SKILL_DIR}/risk_factor_diff.py *), Bash(python ${CLAUDE_SKILL_DIR}/risk_factor_diff.py *)
---

# Risk-factor diff (Playbook, Play 5)

The user gave two saved filings: older `$0`, newer `$1`. If either is missing, ask for both paths and stop.

1. Run the bundled script (standard library only, no network). Run exactly this one command from the current
   directory: no `cd`, no `ls`, nothing chained with `&&` or `;`. Only this exact form is pre-approved.

   `python3 "${CLAUDE_SKILL_DIR}/risk_factor_diff.py" "$0" "$1" --json`

   If `python3` is not found (common on Windows), run the same single command with `python` instead of `python3`.
2. Read the JSON. Check `scope`: if it says Item 1A was not found, tell the user the comparison covered the whole document and may be noisy.
3. Write a short report with these sections, quoting the filing text exactly:
   - **Certainty shifts** (could/may language that became has/had): list each with the word-level diff.
   - **New risks** (added headings and paragraphs).
   - **Removed risks**, and for each, whether the same idea appears reworded elsewhere in the new filing (search the new file with Read before calling it gone).
   - **Material wording changes** (changed paragraphs with similarity below 0.9 first).
   - **Moved headings.**
4. For every added or changed item, write one research question: *what event or fact would explain this change, and where would it show up (MD&A, an 8-K, the notes)?*
5. End with the counts line from the script and the disclaimer below.

## Guardrails

- This is a reading aid. Do not draw investment conclusions, do not say whether a change is good or bad for the stock, and never suggest buying or selling anything.
- Quote filings exactly; do not paraphrase risk language inside quotation marks.
- Do not fetch anything from the internet. Work only on the files the user provided.

*Educational only. Not investment advice. Independent; not affiliated with any fund or firm.*
