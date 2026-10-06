# AllesSandro

The base every sandrogekeler project is set up from and kept in step with: CI
and security workflows, PR and label conventions, agent docs and Claude Code
config, and the health-check runner. It is a [Copier](https://copier.readthedocs.io)
template; [Renovate](https://docs.renovatebot.com/modules/manager/copier/) opens
an update PR in every connected repo when a new version is tagged here.

```
change here → tag vX.Y.Z → Renovate opens "Update AllesSandro template" PRs → each repo's CI runs → merge
```

## Two kinds of file

| Tier | What | On a template update |
|---|---|---|
| **Locked** | `.claude/suite-*.py`, `.github/workflows/{codeql,scorecard,pr-labelled,labels,template-guard}.yml`, optional `aislop.yml`, `claude.yml`, `.aislop/base.yml`, `.github/scripts/release-notes.py`, `.claude/rules/template-files.md` | Re-applied. A local edit is kept but shows as a merge conflict ([docs/updating.md](docs/updating.md)). |
| **Seeded** | `CLAUDE.md`, `agent_docs/*`, `.claude/settings.json`, `.claude/suite.json`, `.github/{dependabot.yml,labels.json,…}`, README, CONTRIBUTING, SECURITY, ignores, `lefthook.yml`, `renovate.json` | Created once, then owned by the project. Never touched again. |

The list of seeded paths is `_skip_if_exists` in [`copier.yml`](copier.yml).

## Per-project flexibility

Answers to the template's questions (`copier.yml`) shape what a repo gets: the
project kind, its languages (CodeQL matrix, Dependabot ecosystems, health
commands), the tracker, and whether aislop, the @claude action and release
notes are on. They are stored in each repo's `.copier-answers.yml`.

## Docs

- [docs/adopting.md](docs/adopting.md): set up a new repo, or connect an existing one
- [docs/updating.md](docs/updating.md): release a template change, and resolve conflicts
- [docs/conventions.md](docs/conventions.md): labels, PRs, what belongs here

## Layout

```
copier.yml            questions, seeded list
template/             what a project receives
schemas/              JSON schema for each project's .claude/suite.json
tests/                template render + update tests (run in CI)
```

The health-check runner (`template/.claude/suite-*.py`) and the release-notes
generator came from kollektiv-mc/Kollektiv's suite-kit, byte for byte. Kollektiv
keeps the Minecraft-suite specifics (design tokens, label overlay, mc skills).
