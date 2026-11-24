# Engineering philosophy

Use for code, software repositories, infrastructure, configuration, automation, and technical troubleshooting.

## Execution
- Translate the task into observable checks before implementation.
- Feature: write or identify the acceptance test, then implement the minimum code that passes it.
- Bug: reproduce it with a failing test or deterministic command before fixing it.
- Never say code works without running the relevant checks.

## Design
- Prefer standard language layouts, formatters, linters, test tools, and the standard library.
- One file or module per clear responsibility.
- Avoid speculative settings, abstractions, compatibility layers, and error handling for impossible states.
- Existing project conventions win. Do not rewrite working code merely to match this philosophy.
- Keep secrets and environment-specific configuration out of source code. Commit dependency lock files.

## Web and platform work
- Keep HTML, CSS, and JavaScript separate. Use ES modules and no inline handlers.
- For multiple operating systems, share the portable layer and isolate platform-specific code behind a documented interface.
