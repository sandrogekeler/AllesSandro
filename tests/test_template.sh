#!/usr/bin/env bash
# Renders the template for every project kind and checks the output, then
# simulates a template update over a locally edited project and checks that
# locked files conflict, seeded files are left alone, and the guard catches it.
#
# Needs: copier, check-jsonschema, actionlint, python3 with PyYAML, git.
# Run from the repo root: tests/test_template.sh
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
export GIT_AUTHOR_NAME=test GIT_AUTHOR_EMAIL=test@example.com
export GIT_COMMITTER_NAME=test GIT_COMMITTER_EMAIL=test@example.com

fail() { echo "FAIL: $*" >&2; exit 1; }

# Work on a throwaway clone so the test can commit and tag freely, and so it
# renders exactly what is committed (copier copies from git, not the worktree).
git clone -q "$ROOT" "$WORK/tpl"
git -C "$WORK/tpl" checkout -q "$(git -C "$ROOT" rev-parse HEAD)" 2>/dev/null || true
if ! git -C "$ROOT" diff --quiet HEAD -- . ; then
  echo "note: uncommitted changes in $ROOT are not tested (copier renders from git)"
fi
git -C "$WORK/tpl" tag -f v0.0.1 >/dev/null

render() { # name, extra -d args...
  local name=$1; shift
  copier copy -q --trust --defaults --vcs-ref v0.0.1 -d project_name="Test $name" "$@" "$WORK/tpl" "$WORK/out/$name" >/dev/null
}

check_project() { # dir
  local d=$1
  check-jsonschema -q --schemafile "$ROOT/schemas/project.schema.json" "$d/.claude/suite.json" || fail "$d suite.json schema"
  python3 -c 'import json,sys;[json.load(open(f)) for f in sys.argv[1:]]' \
    "$d/.claude/settings.json" "$d/.github/labels.json" "$d/renovate.json" || fail "$d json"
  python3 -c 'import yaml,sys;[yaml.safe_load(open(f)) for f in sys.argv[1:]]' \
    "$d"/.github/workflows/*.yml "$d/.github/dependabot.yml" "$d/lefthook.yml" "$d"/.github/ISSUE_TEMPLATE/*.yml || fail "$d yaml"
  (cd "$d" && actionlint -no-color .github/workflows/*.yml) || fail "$d actionlint"
  if grep -rnE '^(<<<<<<< before updating|>>>>>>> after updating)$' "$d"; then fail "$d ships conflict markers"; fi
  if grep -rn '{{\|{%' "$d" --include='*.md' --include='*.yml' --include='*.json' | grep -v 'workflows/' | grep -q .; then
    grep -rn '{{\|{%' "$d" --include='*.md' --include='*.yml' --include='*.json' | grep -v 'workflows/'; fail "$d has unrendered jinja"
  fi
  [ "$(wc -l < "$d/agent_docs/CLAUDE.md")" -lt 200 ] || fail "$d agent_docs/CLAUDE.md is over 200 lines"
}

echo "== render every kind"
for kind in wails-desktop vite-web go-service python-service static-site library other; do
  render "$kind" -d kind="$kind"
  check_project "$WORK/out/$kind"
  echo "ok  $kind"
done

echo "== optional parts switch off"
render bare -d kind=other -d aislop=false -d claude_action=false -d release_notes=false
check_project "$WORK/out/bare"
for f in .github/workflows/aislop.yml .github/workflows/claude.yml .aislop .aislopignore .github/scripts/release-notes.py .github/changelog.json; do
  [ ! -e "$WORK/out/bare/$f" ] || fail "bare should not have $f"
done
echo "ok  bare"

echo "== codeql matrix follows languages"
grep -q 'language: go' "$WORK/out/go-service/.github/workflows/codeql.yml" || fail "go missing"
if grep -q 'javascript-typescript' "$WORK/out/go-service/.github/workflows/codeql.yml"; then fail "go-service scans TS"; fi
grep -q 'javascript-typescript' "$WORK/out/vite-web/.github/workflows/codeql.yml" || fail "TS missing"
echo "ok  matrix"

echo "== update: locked conflicts, seeded untouched, guard trips"
P="$WORK/out/go-service"
git -C "$P" init -q && git -C "$P" add -A && git -C "$P" commit -qm init
sed -i "s/cron: '36 14 \* \* 0'/cron: '0 3 * * 1'/" "$P/.github/workflows/codeql.yml"
echo "local roadmap note" >> "$P/agent_docs/ROADMAP.md"
git -C "$P" commit -qam local

sed -i "s/cron: '36 14 \* \* 0'/cron: '15 2 * * 0'/" "$WORK/tpl/template/.github/workflows/codeql.yml.jinja"
echo "- [ ] template-only item" >> "$WORK/tpl/template/agent_docs/ROADMAP.md.jinja"
git -C "$WORK/tpl" commit -qam "test change" && git -C "$WORK/tpl" tag v0.0.2

(cd "$P" && copier update -q --skip-answered --defaults --vcs-ref v0.0.2 >/dev/null 2>&1) || true
grep -q '^<<<<<<< before updating$' "$P/.github/workflows/codeql.yml" || fail "locked edit did not conflict"
grep -q 'local roadmap note' "$P/agent_docs/ROADMAP.md" || fail "seeded file lost its local edit"
if grep -q 'template-only item' "$P/agent_docs/ROADMAP.md"; then fail "seeded file was updated"; fi
grep -q '_commit: v0.0.2' "$P/.copier-answers.yml" || fail "answers not bumped"
if ! (cd "$P" && git grep -qnE '^(<<<<<<< before updating|>>>>>>> after updating)$'); then fail "guard regex misses markers"; fi
echo "ok  update"

echo "all template tests passed"
