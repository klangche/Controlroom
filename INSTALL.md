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
