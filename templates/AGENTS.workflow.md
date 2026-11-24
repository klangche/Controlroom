# Repository workflow

## Planning and issues
- Every goal starts as a plan issue. Ordered sub-issues are the implementation checklist.
- A request without an issue gets an issue before implementation.
- One step equals one issue, one branch, and one pull request. The pull request uses `Closes #<issue>`.
- If issue access is unavailable, put the plan and checklist in the pull request description.

## Labels
- Exactly one type label: `plan`, `enhancement`, `bug`, `documentation`, or `release`.
- Add `breaking` when the pull request title contains `!`.
- Add `blocked` while an open `Blocked by #<issue>` dependency remains.
- A pull request copies its issue labels.

## Branches
- `main` contains tested releases.
- `dev` is the beta channel and default development branch.
- Branch from current `dev`: `feat/<issue>-<slug>`, `fix/<issue>-<slug>`, `docs/<issue>-<slug>`, or `debug/<issue>-<slug>`.
- Normal pull requests target `dev` and are squash-merged by the owner.
- Release pull requests go from `dev` to `main` and use a merge commit.
- Hotfixes branch from and target `main`; after release, merge `main` back into `dev`.
- Merge the target branch into a work branch to update it. Do not rebase or force-push.

## Multiple agents
- Claim only an open, unclaimed, unblocked step without a linked pull request.
- Claim with an issue comment, then re-read the issue. The earliest claim wins.
- Push the branch and open a draft pull request. Draft means in progress; ready means built and checked.
- Planner creates the plan. Builder implements one step. A separate Reviewer reviews it.
- Never merge, approve your own pull request, push directly to `main` or `dev`, change secrets, or weaken repository protections.

## Pull requests
- Title: `Added:`, `Changed:`, `Fixed:`, `Removed:`, or `Security:`. Add `!` for a breaking change.
- The description states what changed, checks and results, unverified items, and the independent review verdict.
- Every pull request adds one Markdown fragment under `changes/`. Release automation consumes the fragments.

## Build and release
- GitHub Actions builds and tests pull requests and both protected branches.
- Every merge into `dev` may publish `vX.Y.Z-beta.N`.
- Releases originate only from `main`. The owner runs the release workflow, which creates `vX.Y.Z`.
- Never create or push release tags locally.
- Use Semantic Versioning. Release notes come from pull request titles and `changes/` fragments since the previous stable release.
- Release archives include `READ_ME_FIRST.txt` when users must run a command or bypass unsigned-package warnings.

## Completion
- The requested behavior works and checks passed, or the pull request clearly lists what could not be verified.
- The pull request closes its issue, independent review is recorded, and required CI is green.
