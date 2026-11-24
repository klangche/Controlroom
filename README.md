# Controlroom

Controlroom is the successor to Repo-Starter. It installs a consistent operating model for humans and AI agents while letting each repository choose which philosophies to follow.

## Before installation: choose what to follow

**This choice happens before Controlroom changes the target repository.** **The Repo-Starter philosophy is mandatory and is Controlroom's base.** Core safety and integrity rules are also mandatory. The additional Controlroom philosophies are selectable.

1. Open [`installer/index.html`](installer/index.html) locally for a clickable selector, or use the terminal wizard:

   ```bash
   python scripts/controlroom.py configure
   ```

2. Choose **All philosophies** or any combination of:
   - Engineering
   - Work
   - Personal
   - Writing
   - Research

3. Review the generated `controlroom.config.json`.
4. Install into a repository:

   ```bash
   python scripts/controlroom.py install /path/to/target-repository --config controlroom.config.json
   ```

Nothing is installed until step 4.

## What Controlroom preserves from Repo-Starter

- English-first repository language
- `AGENTS.md` as the canonical AI entry point
- thin pointers for Claude and GitHub Copilot
- plan → issue → branch → pull request workflow
- `main` for releases and `dev` for beta
- one issue, branch, and pull request per step
- semantic versioning and GitHub Actions releases
- release notes generated from pull request titles
- TDD, debugging, planning, and independent review guidance
- safe install, update, and uninstall with a SHA-256 lock receipt
- project-local `changes/`, `status/`, `BUILD.md`, `STATUS.md`, and `VERSIONS.md`

## Philosophy combinations

| Scenario | Suggested selection |
|---|---|
| Software at work | Repo-Starter + Core + Engineering + Work |
| Personal software | Repo-Starter + Core + Engineering + Personal |
| Professional documents | Repo-Starter + Core + Work + Writing |
| Personal research | Repo-Starter + Core + Personal + Research |
| General-purpose repository | All philosophies |

## Installed structure

```text
AGENTS.md                         Canonical generated instructions
CLAUDE.md                        Pointer to AGENTS.md
.github/copilot-instructions.md  Pointer to AGENTS.md
.controlroom/                    Selected source modules and configuration
.controlroom.lock                Installed-file hashes for safe updates/uninstall
changes/                         One release-note fragment per pull request
status/                          Temporary task status files when needed
BUILD.md                         Build and release contract
STATUS.md                        Work-tracking contract
VERSIONS.md                      Released version history
READ_ME_FIRST.txt                Release archive instructions
languages.csv                    User-facing strings
```

## Commands

```bash
python scripts/controlroom.py configure
python scripts/controlroom.py install TARGET --config CONFIG
python scripts/controlroom.py update TARGET --config CONFIG
python scripts/controlroom.py uninstall TARGET
python scripts/controlroom.py validate TARGET
```

## Compatibility

Controlroom replaces Repo-Starter. During installation or update it detects `.repo-starter.lock`, preserves locally changed files, and writes a new `.controlroom.lock`. It never deletes an edited file automatically.

## Project rule

Everything in Controlroom itself is written in English. A user may ask in Swedish or another language, but generated repository content and replies are English unless the user explicitly requests otherwise.
