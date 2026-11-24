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
