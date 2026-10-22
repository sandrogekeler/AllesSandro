<!--
The title and every Changelog line become release-notes copy: imperative,
sentence case, no trailing period, one line, no em dashes. Say what changed,
not which files moved. One pull request can carry several changes; split only
when a part is risky on its own, has to be revertable on its own, or ships at
a different time.
-->

## Why

<!-- The problem or need this addresses. -->

## What changed

<!-- The shape of the change. Enough that a reviewer knows where to look. -->

## Changelog

<!--
One line per change: - type: text. The type is feature, fix, chore, docs or
skip, by the test in CONTRIBUTING.md. chore and docs are counted in the
release notes, not listed. For example:

- feature: Add a compact sidebar
- fix: Keep the header clear of the window controls

Leave it empty for a single change and the notes use the title and the type:
label instead (the pr-labelled status warns that it did).
-->

## How it was verified

<!-- What you ran and what it said: `python3 .claude/suite-check.py`, tests,
or a manual check in the running app. -->

---

- [ ] A Changelog line per change, or a `type:feature`, `type:bug`, `type:docs` or `type:chore` label for a single change, typed by the test in CONTRIBUTING.md rather than by the verb.
- [ ] Labelled with an `area:`. `pr-labelled` stays pending until it has that and one of the two above.
- [ ] Generated files and lockfiles were regenerated, not hand-edited.
