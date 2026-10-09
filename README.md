# Judge Validation Study

Side-by-side annotation app: what the LLM judge saw (task, code, process log)
next to a 15-failure-mode checklist, for human annotators to independently
re-label each of 19 sampled pipelines. See `scripts/validation_study/app.py`
for the full design notes (blinding, context shown, etc.).

## Run locally

```bash
pip install -r requirements.txt
streamlit run scripts/validation_study/app.py
```

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub (public, or private if you connect a private
   repo through your GitHub account on Streamlit Cloud).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with
   GitHub, click **New app**.
3. Pick this repo and branch, and set **Main file path** to
   `scripts/validation_study/app.py`.
4. Deploy. You'll get a shareable `*.streamlit.app` URL to send annotators.

## Known limitation: storage isn't durable

Streamlit Community Cloud's filesystem resets to whatever's in the git repo
whenever the app's container restarts (which happens after enough idle
time). That means annotations written to `scripts/validation_study/
annotations.json` during a session can be **silently lost** once the app
goes idle and wakes back up — there's no persistent disk across restarts.

Mitigations in place:
- The sidebar has a **"Download annotations.json (backup)"** button —
  annotators (or whoever manages the deployment) should use it periodically
  and especially at the end of a session, not just rely on the live file.
- Periodically pull the downloaded file back into this repo and re-push, so
  the git-committed copy stays current and a restart doesn't roll back
  further than your last backup.

If this needs to run for longer than a few days with multiple annotators,
consider swapping the local-file writes for a small external store (a
Google Sheet, a GitHub-API commit on save, or similar) instead of relying on
manual backups.
