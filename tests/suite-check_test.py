#!/usr/bin/env python3
"""Tests for the memory budget (suite-memory.py) and failure reinterpretation.

Run: python3 plugins/suite-kit/suite-check_test.py

Neither section runs a repo's real commands. The three that do would need the
subprocess mocked, and a test of a mock is a test of nothing; what is covered
here is the text handling on either side of them, which is where both sections
fail silently. A miscount reports a confident wrong number, and a budget nobody
can trust is worse than no budget at all. A failure wrongly reinterpreted as a
skip is the same fault one step further on: skipped is the one result nobody
follows up on, so the rule that decides it is worth pinning down.

The fixtures are built on disk under a temporary directory rather than faked,
because half of what is being tested is which files get found in the first
place, and the other half is a real `git check-ignore` answering about a real
.gitignore.
"""

from __future__ import annotations

import importlib.util
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent


def load(stem: str):
    spec = importlib.util.spec_from_file_location(stem, HERE / f"{stem}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = load("suite-check")
probe = load("suite-probe")
check_mod = load("suite-memory")

failures: list[str] = []


def check(name: str, got: object, want: object) -> None:
    if got != want:
        failures.append(f"{name}\n    got  {got!r}\n    want {want!r}")


def write(root: pathlib.Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def resolved(files: list[tuple[str, int]]) -> dict[str, int]:
    return {rel.replace("\\", "/"): count for rel, count in files}


# ── The two halves agree on their vocabulary ────────────────────────────────
# suite-memory.py redeclares the status constants rather than importing them
# from the runner, which would be a cycle. Nothing but this says they match.
check("pass agrees", check_mod.PASS, runner.PASS)
check("fail agrees", check_mod.FAIL, runner.FAIL)
check("skip agrees", check_mod.SKIP, runner.SKIP)
check("the runner declares the memory section", "memory" in runner.SECTIONS, True)

# ── Line counting ───────────────────────────────────────────────────────────
# splitlines, not a newline count: a file whose last line has no trailing
# newline still costs that line. Konnekt's agent_docs/CLAUDE.md is exactly this
# case, which is why it reads 479 here and 478 to `wc -l`.
check(
    "final line without a trailing newline still counts",
    len(check_mod.strip_html_comments("a\nb\nc").splitlines()),
    3,
)

# ── HTML comments ───────────────────────────────────────────────────────────
# The loader strips block-level comments before injecting the file, so counting
# them would tax the maintainer notes that feature exists to make free.
check(
    "a whole-line comment disappears",
    check_mod.strip_html_comments("keep\n<!-- note -->\nkeep").splitlines(),
    ["keep", "keep"],
)
check(
    "a multi-line comment collapses to nothing",
    check_mod.strip_html_comments("a\n<!-- one\ntwo\nthree -->\nb").splitlines(),
    ["a", "b"],
)
check(
    "a trailing comment leaves its line behind",
    check_mod.strip_html_comments("text <!-- note -->").splitlines(),
    ["text "],
)
check(
    "a blank line is not a comment and survives",
    check_mod.strip_html_comments("a\n\nb").splitlines(),
    ["a", "", "b"],
)
# Comments inside a fence are preserved by the loader, so they cost context.
check(
    "a comment inside a fence is kept",
    check_mod.strip_html_comments("```\n<!-- shown -->\n```").splitlines(),
    ["```", "<!-- shown -->", "```"],
)

# ── Import detection ────────────────────────────────────────────────────────
check(
    "a bare import is found",
    check_mod.imports_in("See @agent_docs/CLAUDE.md for the rest"),
    ["agent_docs/CLAUDE.md"],
)
check(
    "two imports on one line are both found",
    check_mod.imports_in("@a/one.md and @b/two.md"),
    ["a/one.md", "b/two.md"],
)
# The docs are explicit: wrap a path in backticks to mention it without
# importing it. Counting those would inflate every file that documents itself.
check(
    "a code span is not an import",
    check_mod.imports_in("wrap it as `see @README here` to keep it literal"),
    [],
)
check(
    "an import after a closed code span is still found",
    check_mod.imports_in("`a @b.md c` then @real.md"),
    ["real.md"],
)
check(
    "a fenced block is not an import",
    check_mod.imports_in("```\n@docs/thing.md\n```"),
    [],
)
check(
    "a tilde fence closes on its own character",
    check_mod.imports_in("~~~\n@a.md\n```\n@b.md\n~~~\n@c.md"),
    ["c.md"],
)
check(
    "an email address is not an import",
    check_mod.imports_in("ask someone@example.com about it"),
    [],
)

# ── Rule scoping ────────────────────────────────────────────────────────────
with tempfile.TemporaryDirectory() as tmp:
    root = pathlib.Path(tmp)
    write(root, "scoped.md", '---\npaths:\n  - "src/**"\n---\n\nbody\n')
    write(root, "unscoped.md", "# No frontmatter\n\nbody\n")
    write(root, "other.md", "---\ndescription: something\n---\n\nbody\n")
    check(
        "a paths: rule is path-scoped",
        check_mod.rule_is_path_scoped(str(root / "scoped.md")),
        True,
    )
    check(
        "a rule with no frontmatter is not",
        check_mod.rule_is_path_scoped(str(root / "unscoped.md")),
        False,
    )
    check(
        "frontmatter without paths: is not",
        check_mod.rule_is_path_scoped(str(root / "other.md")),
        False,
    )

# ── Resolution over a whole repo ────────────────────────────────────────────
with tempfile.TemporaryDirectory() as tmp:
    root = pathlib.Path(tmp)
    # The shape this check exists for: a short root file importing a long one.
    # Splitting into imports organises the content and reduces the cost by
    # nothing, so both files have to land in the total.
    write(
        root,
        "CLAUDE.md",
        "<!-- maintainer note, stripped before injection -->\n"
        "See @docs/big.md for everything.\n",
    )
    write(root, "docs/big.md", "\n".join(f"line {i}" for i in range(1, 51)) + "\n")
    write(root, ".claude/rules/scoped.md", '---\npaths:\n  - "src/**"\n---\nbody\n')
    write(root, ".claude/rules/always.md", "one\ntwo\nthree\n")

    files, notes = check_mod.resolve(str(root))
    got = resolved(files)
    check(
        "the root file and its import are both counted",
        got,
        {"CLAUDE.md": 1, "docs/big.md": 50, ".claude/rules/always.md": 3},
    )
    check("a path-scoped rule is excluded", ".claude/rules/scoped.md" in got, False)
    check("nothing unexpected was skipped", notes, [])

    status, reason, _ = check_mod.evaluate(str(root), None)
    check("under the default budget passes", status, check_mod.PASS)
    check("the total is reported", reason, "54 of 200 lines")

# ── The budget and its ratchet ──────────────────────────────────────────────
with tempfile.TemporaryDirectory() as tmp:
    root = pathlib.Path(tmp)
    write(root, "CLAUDE.md", "\n".join(f"line {i}" for i in range(1, 301)) + "\n")

    check(
        "over the default budget fails",
        check_mod.evaluate(str(root), None)[0],
        check_mod.FAIL,
    )
    check(
        "an over-budget repo passes on its ratchet",
        check_mod.evaluate(str(root), {"maxLines": 300})[0],
        check_mod.PASS,
    )
    check(
        "a ratchet set below the real total still fails",
        check_mod.evaluate(str(root), {"maxLines": 250})[0],
        check_mod.FAIL,
    )

with tempfile.TemporaryDirectory() as tmp:
    # The ratchet's expiry. The schema refuses a maxLines under 201, but a
    # schema only binds a repo that validates its manifest, so the runner
    # refuses the stale field too: a repo that has arrived must give up its
    # licence to be over budget rather than keep it for later.
    root = pathlib.Path(tmp)
    write(root, "CLAUDE.md", "\n".join(f"line {i}" for i in range(1, 51)) + "\n")
    status, reason, _ = check_mod.evaluate(str(root), {"maxLines": 639})
    check(
        "a repo now inside the budget fails on its stale ratchet",
        status,
        check_mod.FAIL,
    )
    check("and is told to delete the field", "delete health.memory" in reason, True)

# ── A repo with no memory file at all ───────────────────────────────────────
with tempfile.TemporaryDirectory() as tmp:
    status, _, _ = check_mod.evaluate(tmp, None)
    check("no CLAUDE.md is a skip, not a pass", status, check_mod.SKIP)

# ── Cycles and depth ────────────────────────────────────────────────────────
with tempfile.TemporaryDirectory() as tmp:
    root = pathlib.Path(tmp)
    write(root, "CLAUDE.md", "@a.md\n")
    write(root, "a.md", "@CLAUDE.md\n")
    files, _ = check_mod.resolve(str(root))
    check(
        "a cycle terminates and counts each file once",
        resolved(files),
        {"CLAUDE.md": 1, "a.md": 1},
    )

with tempfile.TemporaryDirectory() as tmp:
    # Relative imports resolve against the file holding them, not the repo root.
    root = pathlib.Path(tmp)
    write(root, "CLAUDE.md", "@docs/one.md\n")
    write(root, "docs/one.md", "@two.md\n")
    write(root, "docs/two.md", "body\n")
    files, _ = check_mod.resolve(str(root))
    check(
        "a nested relative import resolves against its own file",
        sorted(resolved(files)),
        ["CLAUDE.md", "docs/one.md", "docs/two.md"],
    )

# ── A //go:embed miss is the environment only when the target is build output ─
# Go compiles embed directives during vet and test, so a package embedding a
# gitignored Vite bundle cannot be checked on a fresh clone. That is the
# environment. An embed naming a tracked file that is simply gone is not, and
# the two arrive as the same error text, so only the tree can tell them apart.

EMBED_MISS = "main.go:15:12: pattern all:frontend/dist: no matching files found\n"


def git_fixture(root: pathlib.Path, ignore: str) -> None:
    write(root, ".gitignore", ignore)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, capture_output=True)


have_git = subprocess.run(
    ["git", "--version"], capture_output=True, check=False
).returncode == 0

if not have_git:
    print("git not available: skipping the //go:embed cases", file=sys.stderr)
else:
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        git_fixture(root, "frontend/dist/\n")
        check(
            "an absent gitignored embed target is build output",
            probe.missing_build_output(EMBED_MISS, str(root)),
            "frontend/dist",
        )
        check(
            "and the whole failure reads as environmental",
            probe.environmental_failure("go vet ./...", str(root), str(root), EMBED_MISS),
            "embedded build output not present (no frontend/dist)",
        )

    with tempfile.TemporaryDirectory() as tmp:
        # Nothing ignores it, so something that should be committed is missing.
        # Reporting that as a skip would bury a genuinely broken tree.
        root = pathlib.Path(tmp)
        git_fixture(root, "node_modules/\n")
        check(
            "an absent tracked embed target stays a failure",
            probe.missing_build_output(EMBED_MISS, str(root)),
            None,
        )

    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        git_fixture(root, "frontend/dist/\n")
        write(root, "frontend/dist/index.html", "<!doctype html>\n")
        check(
            "a target that exists is not the reason for any failure",
            probe.missing_build_output(EMBED_MISS, str(root)),
            None,
        )

    with tempfile.TemporaryDirectory() as tmp:
        # No repo, so check-ignore cannot answer. Guessing here would hide the
        # case this whole rule exists to keep visible.
        root = pathlib.Path(tmp)
        check(
            "outside a git repo the question goes unanswered",
            probe.missing_build_output(EMBED_MISS, str(root)),
            None,
        )

    with tempfile.TemporaryDirectory() as tmp:
        # `go test` keeps going into the packages that do compile, so a real
        # break lands in the same output as the embed miss. Verbatim from
        # Konnekt with a deliberate error added to backend/services.
        root = pathlib.Path(tmp)
        git_fixture(root, "frontend/dist/\n")
        both = (
            "# konnekt\n"
            "main.go:15:12: pattern all:frontend/dist: no matching files found\n"
            "FAIL\tkonnekt [setup failed]\n"
            "?   \tkonnekt/backend/models\t[no test files]\n"
            "# konnekt/backend/services\n"
            "backend/services/eventbus.go:65:26: undefined: undefinedSymbol\n"
            "FAIL\tkonnekt/backend/services [build failed]\n"
            "ok  \tkonnekt/scripts/gen-icons\t(cached)\n"
            "FAIL\n"
        )
        check(
            "a real break alongside the miss is never reinterpreted",
            probe.missing_build_output(both, str(root)),
            None,
        )
        check(
            "a failing test alongside the miss is not either",
            probe.missing_build_output(
                "main.go:15:12: pattern all:frontend/dist: no matching files found\n"
                "--- FAIL: TestThing (0.00s)\n"
                "FAIL\tkonnekt/backend/services\t0.12s\n",
                str(root),
            ),
            None,
        )
        check(
            "but the miss on its own still reads as build output",
            probe.missing_build_output(
                "# konnekt\n"
                "main.go:15:12: pattern all:frontend/dist: no matching files found\n"
                "FAIL\tkonnekt [setup failed]\n"
                "?   \tkonnekt/backend/models\t[no test files]\n"
                "ok  \tkonnekt/backend/services\t6.494s\n"
                "FAIL\n",
                str(root),
            ),
            "frontend/dist",
        )

    with tempfile.TemporaryDirectory() as tmp:
        # The pattern is relative to the .go file's own directory, not the cwd
        # the command ran in.
        root = pathlib.Path(tmp)
        git_fixture(root, "shell/dist/\n")
        write(root, "shell/main.go", "package main\n")
        check(
            "the pattern resolves against the source file's directory",
            probe.missing_build_output(
                "shell/main.go:9:12: pattern dist: no matching files found\n", str(root)
            ),
            "shell/dist",
        )

with tempfile.TemporaryDirectory() as tmp:
    # The reinterpretation is scoped to the toolchain that produces the error.
    root = pathlib.Path(tmp)
    check(
        "a non-Go command is never reinterpreted by the embed rule",
        probe.environmental_failure("./scripts/x.sh", str(root), str(root), EMBED_MISS),
        None,
    )
    check(
        "and a Go failure with other output is still a failure",
        probe.environmental_failure(
            "go vet ./...", str(root), str(root), "backend/x.go:4:2: undefined: Foo\n"
        ),
        None,
    )

# ── The ruff pin comes from the workflow, and only when it is unambiguous ───
# aislop scores nothing for Python without ruff, and says `[ok] 0 issues` while
# doing it, so the runner has to establish before the run that the result would
# mean what CI means. The version it checks against is read from the workflow so
# that nothing here becomes a second place the pin is written.

AISLOP_RUN = "npx --yes aislop@0.16.0 ci"


def pin(root: pathlib.Path, workflow: str, version: str) -> None:
    """Write a workflow that pins ruff the way CI does."""
    write(root, f".github/workflows/{workflow}", f"  - run: pip install ruff=={version}\n")


with tempfile.TemporaryDirectory() as tmp:
    root = pathlib.Path(tmp)
    pin(root, "aislop.yml", "0.16.7")
    check("a product's vendored workflow carries the pin", probe.pinned_ruff(str(root)), "0.16.7")

with tempfile.TemporaryDirectory() as tmp:
    # kollektiv is not a product, so it carries the same steps inline in ci.yml.
    root = pathlib.Path(tmp)
    pin(root, "ci.yml", "0.16.7")
    check("kollektiv's inline copy is found too", probe.pinned_ruff(str(root)), "0.16.7")

with tempfile.TemporaryDirectory() as tmp:
    # Two workflows disagreeing is a real problem, but picking one of them would
    # be the confident wrong number this runner exists not to produce.
    root = pathlib.Path(tmp)
    pin(root, "a.yml", "0.16.7")
    pin(root, "b.yml", "0.15.8")
    check("disagreeing pins answer nothing", probe.pinned_ruff(str(root)), None)

with tempfile.TemporaryDirectory() as tmp:
    root = pathlib.Path(tmp)
    check("no workflows directory answers nothing", probe.pinned_ruff(str(root)), None)

with tempfile.TemporaryDirectory() as tmp:
    root = pathlib.Path(tmp)
    write(root, ".github/workflows/aislop.yml", f"  - run: {AISLOP_RUN}\n")
    check("a workflow with no pin answers nothing", probe.pinned_ruff(str(root)), None)

# ── A repo that pins ruff only runs aislop against that ruff ────────────────

with tempfile.TemporaryDirectory() as tmp:
    root = pathlib.Path(tmp)
    pin(root, "aislop.yml", "99.99.99")
    gap = probe.aislop_ruff_gap(AISLOP_RUN, str(root))
    check("a ruff that is not the pinned one is named", "99.99.99" in (gap or ""), True)
    check("a command that is not aislop is left alone",
          probe.aislop_ruff_gap("pnpm lint", str(root)), None)

with tempfile.TemporaryDirectory() as tmp:
    # Nothing pinned means nothing to prove, so the run goes ahead. Silence here
    # is the difference between reading a repo's own intent and inventing one.
    root = pathlib.Path(tmp)
    check("an unpinned repo still runs aislop",
          probe.aislop_ruff_gap(AISLOP_RUN, str(root)), None)

# ── Report ─────────────────────────────────────────────────────────────────
if failures:
    print(f"{len(failures)} failing:\n", file=sys.stderr)
    for failure in failures:
        print(f"  {failure}\n", file=sys.stderr)
    sys.exit(1)
print("suite-check: all checks passed")
