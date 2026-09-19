# Homepage 1,000-persona run (job 3fffd213) — what survives

The run (`pg-web-infobric-audit-v2-homepage-3fffd213`, launched 2026-09-19 01:04 PDT,
instrument v2.2, persona-browser-use + gpt-5.6-luna, pilot-full cohort `cohort-6c6a64cd6c92`)
reached 886 finished trials (72 failed) before it was stopped at 08:23 PDT through the
cockpit's "Stop batch" button. That button calls the backend's *delete* endpoint, which
removes the job directory; the raw trial data (artifacts, verifier outputs, post-hoc scores)
was lost. No backup destination was configured.

What is kept here, all produced from the live data before the deletion:

| File | Content |
|---|---|
| `summary-at-834-trials.md` | `ablation/summarize_run.py` output at 834 finished / 785 passed: coverage, who was simulated, exit rate vs Quick Backs, six dimensions (mean, sd, distribution) overall and by visitor kind, next steps, quality gates |
| `summary-at-100-trials.md` | the same at 102 finished (early checkpoint) |
| `partner-report-preview-136-trials.md/.json` | `build_partner_report.py` test run on 136 trials, one chunk per visitor kind per text; includes the in-browse vs post-hoc comparison for 107 re-scored trials |
| `ablation-summary-136-trials.md` | ablation summary produced alongside that preview |
| `repaired-artifact-samples/` | four raw `page_audit.json` files with the formatting slips the verifier now repairs |

Numbers quoted in `ablation/findings/exit-and-spread-gaps.md` (803 trials: trait η², exit
rate, anchor echo) and `trust-rating-collapse.md` come from the same data.

Not recoverable: per-trial artifacts, `quality.json`, post-hoc scores, trajectories.
Rerunning the baseline costs ~9 h at concurrency 4.
