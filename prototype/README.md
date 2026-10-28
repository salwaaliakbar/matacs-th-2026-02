# Prototype (optional)

A small script showing the "code decides" half of the design. Standard-library Python only; no AI calls and no API key needed.

| File | What it is |
|---|---|
| [criteria.json](criteria.json) | The admin's criteria for the category: mandatory checks, weights, formulas. Edit this to change the rules; no code changes needed. |
| [extracted.json](extracted.json) | The facts the [extraction prompt](../PROMPTS.md) should return for A–E, entered by hand. Quotes are left out because the brief asks not to copy proposal text. |
| [score.py](score.py) | Mandatory checks → weighted scores → flags → ranking with reasons |

Run it from the repository root:

```bash
python prototype/score.py
```

It writes [../ranking.json](../ranking.json) and prints the points per criterion. Running it again gives an identical file.

**Try a changed requirement:** change a weight or limit in `criteria.json` (for example `"limit": 12` on timeline) and run the script again.
