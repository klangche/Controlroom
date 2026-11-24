## Paste into AI prompt:

```text
Install Controlroom from https://github.com/klangche/Controlroom in this repository.
```

```text
update controlroom
```

```text
Uninstall controlroom
```

Paste one of these into any AI agent connected to your repository (Claude
Code, GitHub Copilot, Codex, Gemini CLI, Cursor, or any agent that can read
a file). A repo-starter install migrates with `update repo-starter` or
`update controlroom`.

# Controlroom

Controlroom is the successor to Repo-Starter. Repo-Starter is the mandatory base philosophy. Controlroom adds selectable philosophies for different kinds of work.

## Install

Give the repository to an AI agent, coding agent, or CLI installer and ask it to install Controlroom.

**The installer must ask before it installs anything.** It must not assume a profile and it must not require the user to open a separate selector or prepare a configuration file first.

The required question is:

> Which Controlroom philosophies should this repository follow?
> 1. All
> 2. Engineering
> 3. Work
> 4. Personal
> 5. Writing
> 6. Research
> You can choose All or any combination, for example Engineering + Work.

Repo-Starter and Controlroom Core are always included and are not optional.

### AI / agent installation

The installing agent must:

1. Read `INSTALL.md`.
2. Ask the philosophy question in the conversation or agent UI.
3. Wait for the user's answer.
4. Record the answer in `.controlroom/config.json`.
5. Install only after the answer has been received.

If the environment supports clickable choices, present **All**, **Engineering**, **Work**, **Personal**, **Writing**, and **Research** as selectable choices. Otherwise ask the same question as plain text.

### CLI installation

Run:

```bash
python scripts/controlroom.py install /path/to/repository
```

The CLI asks the same question interactively before making changes.

For automation only, an explicit preselected configuration may be supplied:

```bash
python scripts/controlroom.py install /path/to/repository --config controlroom.config.json --non-interactive
```

`--non-interactive` is intentionally required when bypassing the question. This prevents an agent or script from accidentally skipping the selection.

## Philosophy model

```text
Mandatory
├── Repo-Starter
└── Controlroom Core

Optional, selected during installation
├── Engineering
├── Work
├── Personal
├── Writing
└── Research
```

Examples:

- software at work: Repo-Starter + Core + Engineering + Work
- personal software: Repo-Starter + Core + Engineering + Personal
- professional writing: Repo-Starter + Core + Work + Writing
- everything: Repo-Starter + Core + all optional philosophies

## Commands

```bash
python scripts/controlroom.py install TARGET
python scripts/controlroom.py update TARGET
python scripts/controlroom.py uninstall TARGET
python scripts/controlroom.py validate TARGET
```

`install` asks before installing. `update` retains the repository's current selection unless the owner explicitly asks to change it.

## Project rule

Everything in Controlroom itself is written in English. The user may communicate in Swedish or another language, but generated repository content and replies are English unless another output language is explicitly requested.

## Update prompt

```text
update controlroom (or: update repo-starter)

1. Get Controlroom: clone https://github.com/klangche/Controlroom (branch
   main) outside this repository, or read the manual steps in its
   INSTALL.md if you cannot run Python 3.10+.
2. Run `python <controlroom>/scripts/controlroom.py self-test`. It fails:
   stop and report; change nothing.
3. Run `python <controlroom>/scripts/controlroom.py update .`. It keeps
   .controlroom/config.json. No selection yet (fresh, or a repo-starter
   install with .repo-starter.lock): ask me the philosophy question from
   INSTALL.md first, as clickable choices if you can, and wait.
4. The "## Project" section of AGENTS.md must be unchanged byte for byte.
   Files listed as preserved stay as they are; list them in the report.
5. Create the labels from AGENTS.md section 6 that are missing, if your
   tools can; skip existing ones. Nothing else in repository settings.
6. One pull request, branch docs/update-controlroom, to dev (to main if
   there is no dev), with a per-file change report. Then stop.
```

## Uninstall prompt

```text
Uninstall controlroom from this repository.

1. Read .controlroom.lock. If it does not exist, stop and ask me: never
   guess what was installed.
2. Run `python <controlroom>/scripts/controlroom.py uninstall .`, or by
   hand: delete each locked file whose sha256 still matches (AGENTS.md:
   text above "## Project"; ask me first); keep changed files.
3. Delete folders left empty, then .controlroom.lock. Touch nothing else.
   Report removed files, kept files and removed folders.
```

## Tokens

The generated `AGENTS.md` is the only thing every session always reads.
Skills add their description line, and their body only when triggered.
Subagents spend no context of the main session. All rules and skills are
files in the repository; the only call out is the version check (one small
file per session), skipped when offline.

## Versions

Line 1 of `MANIFEST.txt` is the version (SemVer). Bump it in every pull
request that changes an installed file, and add one line to `VERSIONS.md`.

## Credits

- Andrej Karpathy-style agent guidelines:
  https://github.com/forrestchang/andrej-karpathy-skills/blob/main/CLAUDE.md
- The AI-native SDLC playbook (Claude Academy):
  https://academy.claude.com/courses/ai-native-sdlc-playbook
- Superpowers by Jesse Vincent (MIT): https://github.com/obra/superpowers
- Ponytail by DietrichGebert (MIT): https://github.com/DietrichGebert/ponytail
- laconic by Gabriel Barberini (MIT): https://github.com/GabrielBarberini/laconic
- repo-starter by klangche, the mandatory base:
  https://github.com/klangche/repo-starter (its "Added by me" list
  carries over: agent-as-installer lifecycle, sha256 receipt, all-agent
  canon split, token rules, portable skills).
