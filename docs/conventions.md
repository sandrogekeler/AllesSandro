# Conventions

## What belongs here

Anything every project should have, the same way: workflows, the label gate,
agent-doc skeletons, Claude Code settings floor, the health runner. Anything
true of one project or one product family belongs in that project (or in
Kollektiv for the Minecraft suite). If a locked file needs to differ between
projects, it becomes a question in `copier.yml` or moves to the seeded tier.

## Labels

Every PR needs one `type:` label and at least one `area:` label; `pr-labelled`
stays pending until both are on. The taxonomy is seeded as
`.github/labels.json` and applied by the `labels` workflow.

| Label | Meaning |
|---|---|
| `type:feature` | The project can now do something it never offered. |
| `type:bug` | Existing behaviour was wrong, even if the fix adds code or UI. |
| `type:chore` | No user-visible change: refactors, tests, CI, dependencies. |
| `type:docs` | Documentation only. |
| `area:*` | What the change touches. Projects add their own. |
| `p0`–`p3` | Issue priority. |
| `changelog:skip` | Leave a merged PR out of the release notes. |

Which `type:`: ask "can a user tell?" (no: chore/docs), then "was it meant to
work already?" (yes: bug), else feature.

## Pull requests

Title is release-notes copy: imperative, sentence case, no trailing period, no
em dashes. One concern per PR.

## Agent files

`CLAUDE.md` stays a few lines and imports `agent_docs/CLAUDE.md` (keep under
~200 lines, per Claude Code's guidance). Path-specific guidance goes in
`.claude/rules/*.md` with `paths:` frontmatter so it loads only when relevant.
Anything an agent must always see is a file in the repo, not a plugin:
declaring a plugin in `.claude/settings.json` does not install it in cloud or
unattended sessions.
