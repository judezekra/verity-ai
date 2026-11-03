# Verity

**An AI agent that verifies the real human behind every payment request.**

University of Georgia · MIST 5400 · Jude Zekra, Krish Desai, Pratham Komma, Charlie Mueller

## Current scope: Phase 1 foundation

This is a local classroom prototype, not a production financial security system. The tagline describes the intended product. **There is no AI investigation, identity verification, risk score, recommendation, or payment execution in Phase 1.** No API key is needed. The shared repository is [judezekra/verity-ai](https://github.com/judezekra/verity-ai).

Implemented: a Streamlit dashboard, SQLite initialization, 20 fictional employees, 15 fictional vendors, 100 historical transactions, policy reference, request preview, and three one-click examples. Audit navigation explicitly shows that investigation persistence is not implemented. Historical payments are seed data, not an audit log.

## Run on Windows (PowerShell)

Use Python 3.11–3.13; this foundation was developed with Python 3.13. Run from the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m verity.database
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open http://localhost:8501 in your browser. Stop the server with Ctrl+C. Using the interpreter directly avoids PowerShell activation-policy issues. The database initialization command is optional: the app creates and seeds it automatically on first launch. Subsequent runs preserve data.

If `.venv` is already installed in this workspace, only the last command is needed. If virtual-environment creation reports an `ensurepip` error but its Python executable exists, bootstrap pip using the installed system pip:

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
2. Click **Routine vendor payment**, then **Preview request**. The preview is plain text, with no fabricated investigation result.
3. Submit blank text to see validation. Load each other sample and preview it.
4. Browse **Company records**, filter employees by department, and select a vendor to see prior transactions.
5. Filter **Transaction history** to Cancelled; five records should appear.
6. Read **Policies & roadmap** and the **Audit log** empty state.

Automated tests cover record counts, foreign keys, amount constraints, repeat initialization, parameterized vendor queries, request boundaries, and the Streamlit navigation/submission workflow. These are foundation checks, not fraud-detection evaluation. AI accuracy and target performance have not been measured.

## Project structure

```text
app.py                    Streamlit views and request-preview session state
verity/database.py        SQLite connection, schema, initialization, read queries
verity/seed.py            Reproducible fictional company records
verity/policies.py        Shared policy configuration (reference only so far)
verity/requests.py        Sample messages and request-input validation
tests/test_foundation.py  Database and Streamlit interaction checks
.streamlit/config.toml    Navy/teal theme, localhost binding, telemetry disabled
.env.example              Blank placeholder for a Phase 2 Claude credential
requirements.txt          Python dependencies
docs/COLLABORATION.md      Private GitHub setup and four-person workflow
log.md                    Completed work and design decisions
tasks.md                  Open work only
data/verity.sqlite3       Generated local database; ignored by Git
```

SQLite is Python's built-in database library. UI code calls a database adapter rather than constructing SQL. Money is stored in integer cents. Vendor payment history is derived from transactions, avoiding inconsistent duplicate histories. Policy text derives its $50,000 threshold from one constant; actual enforcement will be added in Phase 3. Seed dates are fixed in 2026 so demonstrations remain reproducible. The schema version prevents silently opening a database from an unsupported version.

## Synthetic data and safeguards

All records are fictional. Email addresses use `.example`, trusted phone numbers use the fictional 202-555-01xx range, and payment accounts begin with `DEMO-ACCOUNT`. No messages are sent. Request text is treated as text, never executable HTML, SQL, or instructions. Preview text lives in Streamlit session memory and is not saved to SQLite. Database queries use fixed SQL and bound parameters. Detailed startup errors are logged in the terminal, not shown in the interface.

The app binds to localhost and has no authentication: do not expose it publicly or enter private financial data. The database is not encrypted and belongs only to this synthetic demo. `.env`, local databases, keys, environments, and caches are ignored. Phase 1 does not load `.env` or make Claude API calls. `python-dotenv` is included for the next phase. Never commit a populated credential file.

## Troubleshooting

- **Module not found:** install requirements using the same `.venv` interpreter used to run the app.
- **Package installation cannot reach PyPI:** check connectivity/proxy settings, then rerun installation; no API key fixes a package-network issue.
- **Database cannot load:** inspect the terminal error. Stop other running copies if the file is locked. Preserve any database you need; move it to a backup location before recreating the demo. There is no destructive reset button.
- **Port occupied:** add `--server.port 8502` to the Streamlit command and open that port.
- **OneDrive interference:** pause synchronization during the demo or copy the project to a local non-synced folder, then create a fresh environment there.

## Next phases

Phase 2 adds Claude, validated structured extraction, evidence tools, and a clearly labeled deterministic offline mode. Phase 3 completes simulated trusted-contact verification, policy rules, risk scoring, human review, and the audit log. Phase 4 adds 40 scenarios and honest, separate live-AI/offline measurements. Phase 5 adds the business case, cost assumptions, ethics, and final write-up. See `tasks.md`. Stop at Phase 1 review before implementing these.

Course schedule: live demo during the week before Thanksgiving 2026; prototype and write-up due December 1, 2026.

## References

- [Streamlit app testing](https://docs.streamlit.io/develop/api-reference/app-testing)
- [GitHub collaborator invitations](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/inviting-collaborators-to-a-personal-repository)
