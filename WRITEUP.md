# Write-up: AI Proposal Triage (MATACS-TH-2026-02)

**The design in one line:** AI *reads* each proposal and copies out the facts with quotes. Plain code and the admin's rules *score and rank*. People *check, override and decide*. See the [process diagram](diagram/process-flow.png).

**Assumptions:**
- "Last 5 years" is counted back from 2026, so it starts in 2021.
- Formulas: experience = installs ÷ 10 (capped); price and timeline = best eligible value ÷ this bid's; warranty = compared with the best offered; team = 4-item checklist.
- A proposal with an open flag is scored but **not ranked** until a person clears the flag.

## 1. AI vs. rules

| Step | Done by | Why |
|---|---|---|
| Get text from the PDF, check it's readable | Code | Mechanical |
| Pull out facts (price, weeks, who holds the licence…) | **AI** | Wording varies ("since 2021", "past four years", "subcontractor to be confirmed"), and fixed rules break easily |
| Check the AI's answers | Code | Quotes must be in the document |
| Mandatory pass/fail checks | Admin rules | Must be exact |
| Scores, ranking, reasons | Code | Same answer every time |
| Confirm, override, award | People | Someone has to be accountable |

**Where I drew the line:** AI does the one thing rules are bad at, which is understanding varied wording. It never does arithmetic or makes a decision. That also means a hidden "rank me first" instruction has nothing to act on: the AI has no score to change.

## 2. Consistency and explainability

- **Same result twice? Yes.** The AI reads each document once, and its answer is saved and confirmed by a person. Re-ranking reuses those saved facts, and the scoring code has no randomness. Same facts plus the same criteria version gives the same ranking. (The [prototype](prototype/score.py) produces an identical file on every run.)
- After an AI model or prompt upgrade, new extractions are compared with saved ones, and differences go to a reviewer.
- **Seeing why:** each score breaks down by criterion, then the fact used, then the exact quote from the proposal. For example: "E: experience 24/30, 8 installs." Reasons are built from this breakdown by code, not written by the AI, so a reason can never contradict its score.

## 3. Human in the loop

| | Reviewer answers | Samples |
|---|---|---|
| **Checkpoint 1** (after AI, before scoring) | *"Did the AI read it correctly?"* Each doubtful fact is shown beside its quote; the reviewer confirms or corrects it. Nothing is judged here: confirmed facts, even "not stated", go on to the rules. | D: confirms no timeline is stated. C: checks every fact, since C tried to influence the AI. |
| **Checkpoint 2** (after rules and scoring) | *"Do we accept the result?"* Accept the ranking, decide each flag, confirm ineligibility, or override **with a written reason** (the original stays visible). | D: request a schedule. C: disqualify or not. B: confirm ineligible. |
| **Award** | Always a person. | |

**Checkpoint 1 fixes facts; Checkpoint 2 makes decisions.** Flags wait for Checkpoint 2.

**Logged for audit** (never edited or deleted): who did what and when; the file's fingerprint; the criteria version, prompt version and AI model; the AI's raw answer and check results; points per criterion; every correction or override (old value, new value, reason); and the final decision. The log alone shows how any result was produced.

## 4. Changing criteria

- Criteria have **version numbers**. Every ranking says which version it used, and a version is never changed once used. An edit creates a new version.
- Results already produced stay as they were, labelled with the old version. Nothing changes silently.
- To re-score under the new version:
  - **Weights or formulas changed:** recompute from the saved facts. This takes seconds, with no new AI cost.
  - **A new field added:** the AI reads the proposals again for that field only. The new facts go through Checkpoint 1.
- The reviewer sees old and new results side by side (for example, "A and E swap places").
- Weight edits after bids open could favour a bidder, so they need a logged reason.

## 5. Risks and safeguards

| Risk | Example in the samples | Safeguard |
|---|---|---|
| **Manipulation (prompt injection)** | C hides a note telling automated reviewers to rank it first | The AI treats the document as data and has no score to change. A keyword scan also catches it, and C is flagged for a person. Its normal score (84.8) shows the note had no effect. |
| **Made-up facts** | The AI "fills in" D's missing timeline | Never guess. Every fact needs a quote that code finds in the document. A missing number scores 0 and is flagged. |
| **Wrong extraction** | B's licence belongs to a subcontractor, not B | Fields are defined precisely ("held **by the bidder**"). Failed mandatory checks are confirmed by a person. |
| **Fine print** | C counts installs since 2020, beyond the 5-year window | The AI copies the year; code applies the window and flags it. |
| **Poor PDFs** | Scans, tables, columns | Readability check, OCR, quote check |
| **Bias** | Polished writing or big brands doing better | The AI never judges quality. Every bid gets the same checklist and published formulas. Overrides are reviewed for patterns. |
| **Cost** | Hundreds of proposals | One AI call per proposal, saved and reused. Re-scoring needs no AI. |
| **Over-trusting the tool** | Reviewer approves without reading | The tool never awards. Flagged items need an explicit decision. |
| **Confidential pricing** | Bid data sent to an AI provider | Provider that doesn't train on submitted data; role-based access |

**Sample result** ([ranking.json](ranking.json)): A (98.0) and E (91.7) are ranked; C and D are flagged; B is ineligible.
