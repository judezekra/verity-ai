# Verity

**An AI agent that verifies the real human behind every payment request.**

University of Georgia · MIST 5400 · Jude Zekra, Krish Desai, Pratham Komma, Charlie Mueller

## Current scope: Phase 2 investigation

This is a local classroom prototype, not a production financial security system. The tagline describes the intended product. **There is no real identity verification, risk score, payment recommendation, or payment execution yet.** The default offline investigation works without an API key. The shared repository is [judezekra/verity-ai](https://github.com/judezekra/verity-ai); `codex/phase-2-investigation` includes both phases. Feature-branch pushes do not automatically change `main`.

Implemented: a Streamlit dashboard, SQLite, 20 fictional employees, 15 vendors, 100 historical transactions, request preview, three samples, structured extraction, sender/vendor/policy findings, evidence summaries, and tool activity. Offline mode uses deterministic rules, not AI. Optional live mode uses OpenAI through a replaceable adapter; Claude is no longer required. Results exist in the session only. Audit persistence remains Phase 3 work.

## Run on Windows (PowerShell)

Use Python 3.11–3.13; tested here with Python 3.13. For a fresh clone, first run `git switch codex/phase-2-investigation`. Run from the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m verity.database
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open http://localhost:8501 in your browser. Stop the server with Ctrl+C. Using the interpreter directly avoids PowerShell activation-policy issues. The database initialization command is optional: the app creates and seeds it automatically on first launch. Subsequent runs preserve data.

This workspace already has the updated dependencies installed: only the last command is needed. If Streamlit was running during an update, stop it with Ctrl+C and restart. Other teammates should install requirements after pulling updates. If virtual-environment creation reports an `ensurepip` error but its Python executable exists, bootstrap pip using the installed system pip:

```powershell
python -m pip --python .venv\Scripts\python.exe install pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On macOS/Linux, use `python3 -m venv .venv` and `.venv/bin/python` in place of the Windows interpreter path.

## Test and try it

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

1. Confirm the dashboard shows 20 employees, 15 vendors, and 100 historical payments.
2. Leave **Investigation mode** on **Offline demo (no AI)**. Click **Routine vendor payment**, then **Investigate request**. See actual directory/vendor evidence and the continuing human-review requirement.
3. Try **Executive impersonation** for sender mismatch and approval findings, then **Vendor account change** for independent-verification and unusual-amount findings. Inspect All findings, Request & matched records, and Tool activity. Submit blank text to see validation.
4. Browse **Company records**, filter employees by department, and select a vendor to see prior transactions.
5. Filter **Transaction history** to Cancelled; five records should appear.
6. Read **Policies & roadmap** and the **Audit log** empty state.

Automated tests cover database integrity, UI interaction, policy boundaries, ambiguous input, directory conflicts, cancelled history, account mismatch, injection phrases, fabricated extraction, invalid API output, API failure, and tool budgets. Mocked provider calls test the live adapter contract without paid requests. These are software checks, not the planned 40-scenario fraud evaluation. Live model accuracy, cost, and latency have not been measured.

Results describe the submitted request shown in the result panel. Editing the text requires a new investigation. Loading a different sample or a failed submission clears the previous result. Changing the mode selector does not relabel an existing result: its actual execution mode remains visible.

## Optional live AI

Offline mode needs no key, network call, or AI model. For live mode, create a local `.env` from `.env.example` only if `.env` does not already exist, then enter your API key locally. Never paste it into chat or commit it:

```dotenv
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4.1-mini
```

Restart the app, select **Live AI (OpenAI)**, and check the consent box. Live mode sends the fictional request and matched fictional records to OpenAI, not the entire database. API usage may incur charges. Missing credentials, API errors, refusals, incomplete output, or invalid structured data stop the run; there is no silent fallback to offline mode.

The adapter uses strict Responses function calling, a five-call limit, a 15-second per-request SDK timeout, no automatic retries, and `store=False`. These settings limit the workflow and retained API response state; they do not guarantee zero provider retention or a measured total latency. `OPENAI_MODEL` may be changed to a compatible model available to your account. The API destination is fixed so an environment base-URL override cannot redirect the credential.

**A real credential-backed API run has not been tested.** The adapter is implemented and mock-tested; live execution remains an explicit follow-up in `tasks.md`.

## Investigation tools and limits

| Tool | Current behavior |
| --- | --- |
| `parse_request` | Offline pattern extraction or live model extraction, with source-grounding and sender/amount validation |
| `lookup_directory` | Compares the sender and claimed name against actual fictional directory records |
| `check_vendor_history` | Checks vendor status/account, recent changes, and completed payments; excludes cancelled payments |
| `check_policy` | Applies fixed Python approval, authority, account-change, language, and missing-information checks |
| `summarize_evidence` | Live helper selects existing evidence IDs; summary sentences come from Python findings |
| `send_verification` | Not implemented; trusted-contact challenge is Phase 3 |
| `log_decision` | Not implemented; decision persistence is Phase 3 |

In live mode the model calls the four investigation tools in order and then selects highlights. The application controls the sequence: the model cannot skip checks, redirect queries, write records, or execute arbitrary functions. All findings remain visible regardless of highlights. This is a constrained tool workflow, not an autonomous payment agent.

Offline extraction recognizes exact fixture names, a unique `From:` email, explicit USD amounts, `DEMO-ACCOUNT-####` identifiers, and limited urgency/secrecy phrases. Unknown names, multiple amounts, unsupported currency, and ambiguous information require review. Negation and wording outside these patterns can cause false flags or misses. Quoted extraction grounds what the message says; it does not prove the claims are true.

An amount over three times a vendor's historical mean and a bank change within 30 days are explicit demo heuristics, not proof of fraud. Recency uses the investigation date; the fixed October 30, 2026 sample change will age out. Alert/review counts are not risk scores. Every result still requires human review and identity verification.

## Project structure

```text
app.py                    Streamlit views, mode selection, session state
verity/models.py          Typed extraction and evidence structures
verity/extraction.py      Offline parser and source-grounding validation
verity/tools.py           Pure directory, vendor, and policy rules
verity/investigation.py   Workflow orchestration and database reads
verity/providers.py       Replaceable OpenAI function-calling adapter
verity/ui_investigation.py Evidence summaries and tool results
verity/database.py        SQLite connection, schema, initialization, read queries
verity/seed.py            Reproducible fictional company records
verity/policies.py        Shared fictional policy configuration
verity/requests.py        Sample messages and request-input validation
tests/                   Database, UI, investigation, and provider checks
.streamlit/config.toml    Navy/teal theme, localhost binding, telemetry disabled
.env.example              Blank OpenAI credential and model settings
requirements.txt          Python dependencies
docs/COLLABORATION.md      Private GitHub setup and four-person workflow
log.md                    Completed work and design decisions
tasks.md                  Open work only
data/verity.sqlite3       Generated local database; ignored by Git
```

SQLite is Python's built-in database library. UI code calls a service and database adapter rather than constructing SQL. Money is stored in integer cents. Vendor history is derived from transactions. Policy checks and descriptions share one $50,000 threshold; final approval gates arrive in Phase 3. The service depends on a small `ToolAgent` interface so another provider can replace OpenAI without rewriting the pure rules. Seed dates are fixed in 2026. The existing database schema remains unchanged.

## Synthetic data and safeguards

All records are fictional. Email addresses use `.example`, trusted phone numbers use the fictional 202-555-01xx range, and payment accounts begin with `DEMO-ACCOUNT`. No messages are sent. Request text is treated as text, never executable HTML, SQL, or instructions. Preview text lives in Streamlit session memory and is not saved to SQLite. Database queries use fixed SQL and bound parameters. Detailed startup errors are logged in the terminal, not shown in the interface.

The app binds to localhost and has no authentication: do not expose it publicly or enter private financial data. The database is not encrypted and belongs only to this synthetic demo. `.env`, local databases, keys, environments, and caches are ignored. API errors are sanitized and no credentials are stored in results. Strict schemas, quoted extraction, fixed tool dispatch, and Python checks reduce prompt-injection impact, but do not guarantee reliable interpretation or detection of every attack. No directory match counts as verified identity. Never commit a populated credential file.

## Troubleshooting

- **Module not found:** install requirements using the same `.venv` interpreter used to run the app.
- **Package installation cannot reach PyPI:** check connectivity/proxy settings, then rerun installation; no API key fixes a package-network issue.
- **Database cannot load:** inspect the terminal error. Stop other running copies if the file is locked. Preserve any database you need; move it to a backup location before recreating the demo. There is no destructive reset button.
- **Port occupied:** add `--server.port 8502` to the Streamlit command and open that port.
- **OneDrive interference:** pause synchronization during the demo or copy the project to a local non-synced folder, then create a fresh environment there.

## Next phases

Phase 3 completes simulated trusted-contact verification, final policy gates, risk scoring, human decisions, and the audit log. Phase 4 adds 40 scenarios and honest, separate live-AI/offline measurements. Phase 5 adds the business case, cost assumptions, ethics, and final write-up. See `tasks.md`.

Course schedule: live demo during the week before Thanksgiving 2026; prototype and write-up due December 1, 2026.

## References

- [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling)
- [Structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [GPT-4.1 mini capabilities](https://developers.openai.com/api/docs/models/gpt-4.1-mini)
- [Streamlit app testing](https://docs.streamlit.io/develop/api-reference/app-testing)
- [GitHub collaborator invitations](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/inviting-collaborators-to-a-personal-repository)
