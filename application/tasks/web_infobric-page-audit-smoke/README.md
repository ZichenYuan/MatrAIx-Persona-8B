# Infobric page audit — smoke

Throwaway pipeline check for the "MatrAIx in the Wild" (Infobric) study. One
persona reviews the live Infobric homepage with a cut-down version of the study's
Task B rubric. Proves: Docker web image builds, Playwright agent reaches a live
Swedish site, persona + instruction render, JSON artifact is written, verifier
scores it, results aggregate.

- URL: https://infobric.com/se/
- Output: `/app/output/page_audit.json`
- Agent: `persona-openhands-sdk` (auto)

```bash
uv run python application/scripts/generate_application_job.py \
  --task application/tasks/web_infobric-page-audit-smoke \
  --persona-ids 0042 --model-name openai/gpt-4.1
```
