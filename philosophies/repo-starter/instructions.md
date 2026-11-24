# Repo-Starter philosophy

This is the mandatory base philosophy for Controlroom. Optional Controlroom philosophies extend it; they do not replace, weaken, or override it.

## Authority and precedence
- The repository owner is always a human, never an AI.
- Only the owner changes canonical repository rules, except through an explicit setup/update pull request the owner merges.
- Caution over speed. Use judgment for trivial work.
- Precedence: think-before-coding, simplicity, surgical changes, and goal-driven execution first; role-specific skills second; lifecycle structure third. Git/GitHub, release, and safety rules override all of them.

## Language
- Everything is English: replies, code, comments, commits, pull requests, documentation, file names, and logs.
- User-facing translations use stable keys, English as source and fallback, and never the English sentence as the key.

## Think before coding
- State assumptions. If materially unsure, stop and ask.
- If several interpretations exist, list them and ask.
- Point out simpler approaches and important trade-offs.
- Push back when the requested approach is wrong, unsafe, or unnecessarily complex.
- Once the owner decides language, stack, design, or another material choice, proceed without asking again.

## Simplicity first
- Write the minimum code needed for the requested outcome.
- Do not add features, abstractions, settings, compatibility layers, or impossible-state handling that nobody requested.
- If a senior engineer would call the solution overcomplicated, simplify it.

## Surgical changes
- Touch only what the task requires.
- Do not reformat or improve unrelated code.
- Match existing style and remove only what the current change made unused.
- Every changed line must trace to the request or issue.

## Goal-driven execution
- Convert work into observable checks: tests, commands, or expected output.
- For a bug, reproduce it first, then make that reproduction pass.
- Use a short plan with one check per step and continue until the checks pass.
- Never claim success without running the relevant check. If it could not be run, say so.

## Context budget
- Estimate required context before starting. Above roughly 60% of the available session budget, split or hand off the work.
- Load skill bodies only when they trigger.
- Use subagents for heavy or parallel work and hooks for deterministic rules when the environment supports them.
- Prefer quiet test/build/lint commands and inspect verbose output only on failure.

## Repository and workflow
- Separate repositories are the default. Use a monorepo only when applications share code, API, or launcher strongly enough to justify it.
- Cross-repository goals belong in a GitHub Project.
- Every goal starts as a plan issue. Ordered sub-issues are its checklist.
- One step = one issue = one branch = one pull request. The pull request closes its issue.
- Exactly one type label: `plan`, `enhancement`, `bug`, `documentation`, or `release`. Add `breaking` and `blocked` when applicable.
- `main` contains tested releases. `dev` is the beta channel and default development branch.
- Normal work branches from current `dev` using `feat/`, `fix/`, `docs/`, or `debug/` plus issue number and slug. Pull requests target `dev`; the owner squash-merges.
- `dev` to `main` uses a release pull request and merge commit. Hotfixes branch from and target `main`, then `main` is merged back to `dev`.
- Keep work branches current by merging their target branch. Do not rebase when it would require force-pushing. Never force-push.
- Multiple agents claim only available, unblocked work; earliest claim wins. A draft pull request means in progress; ready for review means built and checked.
- Planner plans. Builder implements one step. A different agent instance reviews.
- Debugging records diagnosis and proposed fix before implementation.
- If issue access is unavailable, put the plan and checklist in the pull request description.
- AI agents never merge, approve their own pull requests, push directly to `main`/`dev` except setup creation of `dev`, change secrets, or alter protection/rulesets. Repository labels may be created only during setup/update as explicitly allowed.

## Pull requests
- Description contains what changed, checks and results, what could not be verified, and the independent review verdict.
- Titles use `Added:`, `Changed:`, `Fixed:`, `Removed:`, or `Security:` and `!` for breaking changes.
- Release notes derive from pull request titles and the repository's change-fragment mechanism.

## Code
- Choose the right language for each part and briefly explain why; the owner decides.
- Follow the language's standard layout, formatter, linter, and test tool.
- One file per responsibility where practical.
- Web projects keep HTML, CSS, and JavaScript separate, use ES modules, and avoid inline scripts/styles/handlers.
- Multi-platform software shares the portable layer and isolates platform-specific code behind a documented interface.
- Existing project conventions win. Never rewrite functioning code merely to conform.
- Keep secrets/configuration out of source code, commit lock files, and prefer standard libraries.

## Build and release
- Release builds happen in GitHub Actions, not as local release builds.
- CI builds/tests pull requests and changes headed to `dev` and `main`.
- A merge into `dev` may publish `vX.Y.Z-beta.N`; stable releases originate only from `main` through the owner-run release workflow.
- Never create or push release tags locally. Use Semantic Versioning.
- Stable release notes cover changes since the previous stable release, not merely the previous beta.
- Include `READ_ME_FIRST.txt` when installation requires terminal commands or unsigned-package instructions.
- Default distribution expectations: Windows `.msi`; one universal macOS build; Linux only when requested.

## Safety
- Never commit passwords, tokens, keys, certificates, or other secrets. Use repository/Actions secrets.
- Ask before destructive operations including delete, reset, force-push, and uninstall.

## README
- The project README is about the project: purpose, features, install, usage, platforms, development, and license.
- Its only required reference to repository rules is: `Contributors and AI agents follow AGENTS.md.`

## Done and style
- Done means verified, or explicitly states what remains unverified; the issue is closed by the merged pull request; independent review is recorded; required CI is green.
- Be short, direct, and plain. Avoid marketing language and emojis.
- Chat replies start with TL;DR and then concise bullets.
- If unsure, say so rather than guessing.

## Installation ownership
- Controlroom owns only paths recorded in its manifest/lock receipt.
- Installation/update records SHA-256 hashes. Project-specific content below `## Project` is preserved across updates.
- Uninstall removes an installed file only when its recorded hash still matches; edited files remain.
- Without a valid lock receipt, stop rather than guessing what to remove.
