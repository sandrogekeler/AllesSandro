# Adopting AllesSandro

Requires `pipx install copier` (or `pip install copier`), version 9.4 or later.

## A new repo

1. Create the empty repo on GitHub and clone it.
2. In it: `copier copy --trust gh:sandrogekeler/AllesSandro .` and answer the
   questions. `--trust` is not needed today (the template runs no tasks) but is
   harmless.
3. Commit everything, including `.copier-answers.yml`, and push to `main`.
4. One-time repo settings (GitHub has no account-wide defaults for these on a
   personal account):
   - Install the [Renovate app](https://github.com/apps/renovate) on the repo.
   - Add a ruleset on `main` requiring `pr-labelled`, `template-guard` and
     `renovate/artifacts` (rulesets are free on public repos).
   - Turn on private vulnerability reporting, secret scanning and push protection.
   - If `claude_action` is on: install the [Claude GitHub App](https://github.com/apps/claude)
     and add `ANTHROPIC_API_KEY` or `CLAUDE_CODE_OAUTH_TOKEN` as a repo secret.
   - Run the `labels` workflow once (Actions tab, "Run workflow") to create the labels.
5. Fill in the TODOs in `agent_docs/`.

Or ask Claude in the Master Project: "set up <repo> with AllesSandro".

## An existing repo

Run step 2 in the existing checkout on a branch. Copier asks before
overwriting each existing file; for a seeded file you already have, keep yours.
Review the diff, then continue from step 3. Expect to move project specifics
out of locked files (a locally edited locked file will conflict on every
update until it matches the template or the change moves into AllesSandro).
