CONTROLROOM

Ask your AI agent, coding agent, or CLI to install Controlroom into the target repository.

Before changing anything, the installer must ask:

Which Controlroom philosophies should this repository follow?
- All
- Engineering
- Work
- Personal
- Writing
- Research

Any combination is allowed. Repo-Starter and Controlroom Core are always included.

CLI:
  python scripts/controlroom.py install PATH_TO_REPOSITORY

The CLI asks the question before installation. A separate browser selector is not required.
