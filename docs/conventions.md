# Conventions

## What belongs here

Anything every project should have, the same way: workflows, the label gate,
agent-doc skeletons, Claude Code settings floor, the health runner. Anything
true of one project or one product family belongs in that project (or in
Kollektiv for the Minecraft suite). If a locked file needs to differ between
projects, it becomes a question in `copier.yml` or moves to the seeded tier.

## Labels

Every PR needs at least one `area:` label and either a `## Changelog` section
(see Pull requests) or one `type:` label; `pr-labelled` stays pending until it
has both halves. A PR with a `type:` label and no section passes with a warning
that the release notes will use its title, so a branch rule requiring
`pr-labelled` still lets it merge. The taxonomy is seeded as
`.github/labels.json` and applied by the `labels` workflow.

| Label | Meaning |
|---|---|
| `type:feature` | The project can now do something it never offered. |
| `type:bug` | Existing behaviour was wrong, even if the fix adds code or UI. |
| `type:chore` | No user-visible change: refactors, tests, CI, dependencies. |
| `type:docs` | Documentation only. |
| `area:*` | What the change touches. Projects add their own. |
| `p0`–`p3` | Issue priority. |
| `changelog:skip` | Leave a merged PR out of the release notes, section and all. |

Which type, for a Changelog line or a `type:` label: ask "can a user tell?"
(no: chore/docs), then "was it meant to work already?" (yes: bug, written
`fix` in a Changelog line), else feature.

## Priority

Every issue carries exactly one of `p0`-`p3`:

| Label | Means |
|---|---|
| `p0` | Drop everything. |
| `p1` | High priority, next up. |
| `p2` | Medium priority, normal queue. |
| `p3` | Low priority, nice to have. |

The seeded issue forms ask "How urgent is this for you?" and the locked
`issue-priority` workflow turns the answer into a label when the issue opens:
*Blocking* is `p1`, *Significant* is `p2`, *Minor* is `p3`. `p0` is never
offered; it is a triage call, and triage may move any of the others. An issue
opened through the API has no form answer, so whoever files it, usually an
agent, sets the label in the same call. When none does, the workflow comments
instead of guessing. Unclear means `p2`, never nothing.

The dropdown's label and options must keep the heading and leading words the
workflow matches (`HEADING`, `PRIORITY_MAP`). A project that rewords its forms
keeps those.

## Pull requests

One PR per piece of work, not per tweak. Its body's `## Changelog` section
lists each change on its own line, and the release notes list each line under
the section its type names:

```markdown
## Changelog

- feature: Add a compact sidebar
- fix: Keep the macOS header clear of the traffic lights
- chore: Build with Go 1.26.10
```

Types: `feature`, `fix` (or `bug`), `chore`, `docs`, `skip`. `chore` and `docs`
lines are counted in the notes' footer, not listed; `skip` lines are left out.
A line the gate cannot read (unknown type, no text) holds `pr-labelled` pending
and names the line. Split a PR only when a part is risky on its own, has to be
revertable on its own, or ships at a different time.

Without a section, the PR is one change: its `type:` label files it and its
title is the line. That is how Dependabot and Renovate PRs are filed.

Each Changelog line and every title is release-notes copy: imperative, sentence
case, no trailing period, no em dashes.

`.github/scripts/changelog-section.py` is the one parser. The release-notes
generator loads it from beside itself and `pr-labelled` fetches it from the base
branch, so the gate and the notes read a line the same way. It is locked and
ships whether or not a project generates release notes, because the gate needs
it either way.

## Agent files

`CLAUDE.md` stays a few lines and imports `agent_docs/CLAUDE.md` (keep under
~200 lines, per Claude Code's guidance). Path-specific guidance goes in
`.claude/rules/*.md` with `paths:` frontmatter so it loads only when relevant.
`.claude/rules/writing.md` has no `paths:`, so it loads in every session: it
sets how anything written for a reader reads.
Anything an agent must always see is a file in the repo, not a plugin:
declaring a plugin in `.claude/settings.json` does not install it in cloud or
unattended sessions.

`.claude/rules/simplicity.md` also loads in every session: the code limits (no
abstraction with one user, no unused option, no second way, no code without a
caller) and the wording limits (test names 60 characters, scanned labels 20,
inline messages 140). The numbers are the convention; a project gates them with
its own tests where it has the surface.

Docs describe what is on disk, in the present tense. Intent goes in the roadmap.

## Cloud setup script

A project whose Claude Code cloud sessions need a tool installed keeps the
environment's setup script in the repo, as `scripts/cloud-setup.sh`, and pastes
it into the environment's Setup script field when it changes. The copy in the
repo is the reviewable one.

- It installs, it does not build. The clone is fresh every session; building
  is the session's job.
- It fails loudly: it exits non-zero when anything it installed is not runnable
  afterwards, checked on a standard `PATH`. A half-provisioned environment is
  snapshotted and every later session inherits the gap in silence.

## Verifiable release artefacts

A project that publishes a binary somebody downloads carries three things:

- `checksums.txt` beside the binaries. It proves the download arrived intact,
  not that it came from the project.
- A build provenance attestation from `actions/attest`, in the job that
  uploads the exact bytes, with `id-token: write` and `attestations: write` on
  that job. No signing key exists to leak.
- A download page that shows the `gh attestation verify` command and the
  checksum fallback, and says which question each answers.

OS code signing and notarisation are a separate problem. Release workflows stay
per project; this is a requirement, not a shared workflow.
