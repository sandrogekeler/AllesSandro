# Updating projects from AllesSandro

## Releasing a template change

1. Change `template/` (or `copier.yml`) here in a PR. CI renders every project
   kind and simulates an update.
2. After merge, tag `main`: `git tag vX.Y.Z && git push origin vX.Y.Z`.
   Semver: breaking (a question removed, a locked file renamed) bumps major.
3. Renovate sees the new tag and opens "Update AllesSandro template to vX.Y.Z"
   in every repo whose `.copier-answers.yml` points here. Each repo's CI runs.
   Merge them.

Renovate only reads tags, so an untagged change on `main` reaches nobody.

By hand, in a project: `copier update --skip-answered --defaults`. Add
`--vcs-ref vX.Y.Z` to pin a version.

## When an update PR has conflicts

It happens when the project changed a line of a **locked** file that the
template also changed. Copier keeps both, with inline markers (shown indented
here; real ones start at column 0):

```
  <<<<<<< before updating
  (the project's version)
  =======
  (the template's new version)
  >>>>>>> after updating
```

Renovate commits the file with the markers and flags the PR three ways:

1. a red **`renovate/artifacts`** check, "Artifact file update failure";
2. a comment **"⚠️ Artifact update problem"**: "Renovate failed to update an
   artifact related to this branch. You probably do not want to merge this PR
   as-is.", listing the files under "Updating the Copier template yielded N
   merge conflicts";
3. for conflicted files that are new, an **"ℹ️ Artifact update notice"** comment.

The project's own **`template-guard`** check also goes red, and so does the
"template conflicts" line of `python3 .claude/suite-check.py`.

Renovate's source notes that Copier sometimes reports conflicts that are not
real: read the diff before assuming anything was lost.

To resolve: check out the PR branch, pick per file (keep the project's line,
take the template's, or combine), delete the marker lines, push. Pushing to a
Renovate branch makes Renovate stop rebasing it, which is what you want here.

If the same conflict comes back on every update, the local change is really a
project specific: move it into AllesSandro behind a question, or make that
file seeded for everyone.

**Seeded** files never conflict: updates do not touch them.

## Dependabot and locked workflows

Dependabot bumps action SHAs in locked workflows too. That is fine: the next
template update merges cleanly unless AllesSandro changed the same line. Keep
the pins here current so that is rare.
