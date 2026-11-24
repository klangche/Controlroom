# AGENTS.md

Canonical instructions for contributors to Controlroom itself.

## Language
Everything is written in English, including replies, code, comments, commits, pull requests, documentation, file names, logs, and templates.

## Product invariant
Controlroom must preserve the complete Repo-Starter lifecycle while adding pre-install philosophy selection. Repo-Starter is the mandatory base philosophy. Controlroom Core is mandatory. The installing AI, CLI, or agent must ask the user which optional philosophies to follow before changing the target repository. Installation must not begin until the user answers. Native clickable choices should be used when the host supports them; otherwise ask in chat or the terminal.

## Change rules
- Keep selection modules independent and composable.
- `scripts/controlroom.py` is the reference implementation for configure, install, update, uninstall, and validate.
- Updating generated behavior requires updating templates, tests, `MANIFEST.txt`, and documentation together.
- Never delete an edited target file during update or uninstall.
- Validate with `python scripts/controlroom.py self-test` before claiming completion.

## Workflow
Use plan issues, one issue/branch/pull request per step, change fragments, independent review, `dev` for beta, and `main` for releases. See `templates/AGENTS.workflow.md` for the installed workflow.

## Project
- Goal: Replace Repo-Starter with a context-selectable operating model for human and AI-assisted repositories.
- Users: Developers, knowledge workers, and personal project owners.
- Platforms: Windows, macOS, and Linux with Python 3.10+.
- Stack: Markdown, JSON, HTML/CSS/JavaScript, and Python standard library.
