# Controlroom installation contract

This file is for the AI, CLI, or agent performing the installation.

## Mandatory interaction before installation

Do not install, copy, overwrite, migrate, or modify repository files until the user has answered this question:

> Which Controlroom philosophies should this repository follow?
>
> - All
> - Engineering
> - Work
> - Personal
> - Writing
> - Research
>
> Choose All or any combination. Repo-Starter and Controlroom Core are always included.

If the host supports buttons, checkboxes, quick replies, or another native selection UI, use it. Do not require a web page or separate GUI. If no selection UI exists, ask in normal chat or terminal input.

## Rules

1. Repo-Starter is mandatory and cannot be deselected.
2. Controlroom Core is mandatory and cannot be deselected.
3. Optional philosophies are Engineering, Work, Personal, Writing, and Research.
4. `All` means all five optional philosophies.
5. An empty or ambiguous answer is not consent to install. Ask again.
6. Do not infer a philosophy from repository contents without the user's answer.
7. Save the answer to `.controlroom/config.json` during installation.
8. On update, keep the existing selection unless the owner explicitly requests a new selection.
9. Non-interactive automation may bypass the question only when it supplies an explicit config and explicitly opts into non-interactive mode.
10. Preserve locally modified files according to the SHA-256 lock rules.

## After the answer

Run the equivalent of:

```bash
python scripts/controlroom.py install TARGET
```

and provide the selected philosophies when prompted, or pass the user's explicit answer to the installer through the supported agent/tool interface.

## Agent without Python (manual install)

Same result as the script, for agents that can only read and write files:

1. Download https://raw.githubusercontent.com/klangche/Controlroom/main/MANIFEST.txt .
   Line 1 is `# version X.Y.Z`.
2. For every listed path except `AGENTS.md` (skip `#` lines), download
   `https://raw.githubusercontent.com/klangche/Controlroom/main/<path>` and
   write it unchanged at the same path. Never overwrite a file that is
   not in the manifest, nor a locked file whose sha256 no longer matches.
3. Build `AGENTS.md` by joining, with one blank line between parts:
   `templates/AGENTS.header.md`, the line `# Mandatory Repo-Starter base philosophy`,
   `philosophies/repo-starter/instructions.md`, the line `# Mandatory core`,
   `core/00-language.md`, `core/05-base.md`, `core/10-integrity.md`,
   `core/20-change-control.md`, `core/30-context.md`,
   `templates/AGENTS.workflow.md`, then (if any were chosen) the line
   `# Selected philosophies` and each chosen `philosophies/<name>/instructions.md`,
   then the existing `## Project` section byte for byte, or
   `templates/PROJECT.md` when there is none.
4. Pre-existing `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` or
   `.github/copilot-instructions.md` that Controlroom does not own: quote
   their rules under `## Project` and in the pull request before overwriting.
5. Copy `core/*.md` and the chosen `philosophies/*/instructions.md` (always
   `repo-starter`) to `.controlroom/` at the same relative path, and write
   `.controlroom/config.json` with the answer.
6. Write `.controlroom.lock` as JSON: `schema_version` 1, `product`
   "Controlroom", `version`, `config`, and `files` mapping every written
   path to its sha256. For `AGENTS.md`, hash only the text above `## Project`.
7. Then follow the Setup command in the new `AGENTS.md`.

## Migrating from repo-starter

A repository with `.repo-starter.lock` is migrated by Update:

- Read the plain-text lock (`version X.Y.Z`, then `<path> <sha256>` lines).
  A line that does not parse: stop and ask.
- Ask the philosophy question once (there is no selection yet).
- Files whose hash still matches the old lock are replaced. Changed files
  are kept and listed in the report. `## Project` is kept byte for byte.
- `AGENTS.md` edited above `## Project` since install: stop before
  writing anything and ask the owner to move those edits under
  `## Project`. Half-migrated repositories are not allowed.
- The old lock may list `<path> <sha256>` or `<sha256>  <path>`; accept both.
- repo-starter v1 (no lock, `CLAUDE.md` is a full copy of `AGENTS.md`):
  replace `CLAUDE.md` and the repo-starter files; do not quote them.
- Write `.controlroom.lock`, then rename `.repo-starter.lock` to
  `.repo-starter.lock.migrated`.
