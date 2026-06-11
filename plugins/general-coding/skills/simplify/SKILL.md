---
name: simplify
description: Use when asked to simplify, clean up, refactor, reduce duplication, or improve recent code changes while preserving behavior. Focuses on recently modified files by default, applies project conventions, removes unnecessary complexity, and verifies the result with appropriate tests or checks.
---

# Simplify

Use this skill as a post-change cleanup pass or when the user explicitly asks to simplify code.

## Core Rule

Preserve behavior. Change how the code is expressed, not what it does. If a proposed simplification could alter behavior, skip it or first prove equivalence with tests and local context.

## Scope

Default to recently changed code:

1. Inspect `git status --short` and the relevant diff.
2. Prefer `git diff --stat`, `git diff`, and `git diff -- <path>` over broad repository scans.
3. If the user provides a focus, limit the pass to that feature, file, symbol, or concern.
4. Do not refactor unrelated code unless it is directly needed to simplify the changed code safely.

## Workflow

1. Read project guidance first: local agent instructions, README conventions, formatter/linter/test scripts, and nearby code patterns.
2. Identify cleanup candidates:
   - duplicated logic or data shapes
   - avoidable branching, nesting, or control-flow complexity
   - redundant abstractions, wrappers, state, effects, conversions, or comments
   - names that hide intent
   - inconsistent use of established local helpers or patterns
   - inefficient work introduced by the change, especially repeated parsing, allocation, I/O, or rendering
3. Choose conservative edits:
   - prefer clarity over fewer lines
   - keep useful abstractions that encode domain concepts or isolate change
   - avoid clever one-liners, nested ternaries, and dense chaining when explicit code is easier to scan
   - align with the surrounding style instead of imposing a generic style
4. Apply tightly scoped edits with `apply_patch`.
5. Run the most relevant verification available:
   - existing targeted tests first
   - then lint, type check, formatter check, or broader tests when the change warrants it
   - if checks are unavailable or fail for unrelated reasons, report that plainly
6. Summarize only meaningful simplifications and the verification result.

## Guardrails

- Do not change public APIs, serialized formats, database schemas, migrations, routes, analytics events, or user-visible copy unless the user asked for that scope.
- Do not collapse validation or error handling just because it is verbose.
- Do not remove tests unless they are duplicate coverage and the remaining tests still prove the behavior.
- Do not mix simplification with feature work, dependency upgrades, formatting churn, or broad renames.
- Preserve user changes in the working tree. Never revert unrelated edits.

## Output

Lead with what changed and why. Include verification. If no simplification is worth making, say so and explain the limiting reason in one or two sentences.
