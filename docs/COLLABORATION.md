# Team collaboration

The shared repository is [judezekra/verity-ai](https://github.com/judezekra/verity-ai). Phase 1 is prepared on `codex/phase-1-foundation` for review before merging into `main`. The creation instructions below are retained for reference; skip them for this existing repository.

## Create the private repository (Jude)

On GitHub, choose New repository, name it `verity-ai`, and select **Private**. Leave automatic README, license, and gitignore creation off because this workspace already contains files. Review what will be committed before running these commands from the project directory:

```powershell
git status
git add .
git diff --cached --stat
git diff --cached
git commit -m "Build Phase 1 Verity foundation"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/verity-ai.git
git push -u origin main
```

This workspace already has a Git repository. For a fresh folder without one, run `git init` first. Replace YOUR-USERNAME with the owner's username. Confirm `.env`, `.venv`, and databases are absent from the staged diff. Never put tokens in a remote URL. Authenticate with GitHub's supported sign-in flow.

In repository **Settings → Collaborators**, invite Krish Desai, Pratham Komma, and Charlie Mueller using their actual GitHub usernames or email addresses. Each member must accept. See [GitHub's invitation instructions](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/inviting-collaborators-to-a-personal-repository).

## Each member's workflow

Clone once, create a local Python environment following the README, and work on a separate branch:

```powershell
git clone https://github.com/YOUR-USERNAME/verity-ai.git
cd verity-ai
git switch main
git pull --ff-only
git switch -c krish/claude-investigation
```

Use your own name and a concrete feature in the branch name. Before committing:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
git status
git add verity tests
git diff --cached
git commit -m "Describe the specific change"
git push -u origin krish/claude-investigation
```

Stage the actual files you changed (including documentation when relevant). Open a pull request on GitHub with base `main`; describe behavior, tests, and known limits. Ask another member to review it. Resolve comments, rerun checks, and use **Squash and merge** after approval. Then switch to `main` and `git pull --ff-only` locally before starting another branch. Do not force-push shared branches.

To bring teammates' work into an active branch, commit your changes first, then `git fetch origin` and `git merge origin/main`. Resolve conflicts by reading both versions with the author; remove conflict markers and rerun tests before committing. Never resolve a conflict by blindly discarding someone else's work. Branches isolate work, but changes to the same lines still require coordination.

If repository rules available on your GitHub plan support it, require a pull request and one approval for `main`. Otherwise follow this review agreement manually. Keep each pull request small, agree on function interfaces, and announce changes to shared files such as `app.py` and `requirements.txt`.

## Suggested ownership

| Member | Primary responsibility | Collaboration boundary |
| --- | --- | --- |
| Jude Zekra | Product scope, Streamlit interface, demo coordination | Own `app.py`; review integration changes |
| Krish Desai | Claude adapter, extraction validation, agent tools | Keep API calls outside policy logic |
| Pratham Komma | Database, policy rules, verification and audit | Agree on typed findings with Krish |
| Charlie Mueller | Scenario evaluation, tests, business case and write-up | Review metrics and assumptions with the team |

Ownership coordinates work; everyone should contribute code or documentation and review another person's PR. Read `log.md` and `tasks.md` before starting, record meaningful decisions in `log.md`, and remove finished items from `tasks.md`.
