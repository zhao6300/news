# Agent Rules

- Keep every implementation phase independently testable and narrowly scoped.
- Run `make test` before starting a new phase.
- Do not introduce dependencies without explaining the reason.
- Stop expanding a phase after three related test failures; record the next actionable step.
- Every successful phase must produce a focused local commit.

## Project Rules

Language and interfaces:

- User-facing text and operational documentation must be in Chinese; identifiers and path names remain in English.
- The Web UI must accept either signed or unsigned URL paths; route parsing normalizes them through `_path_segments`.
- Do not add a second UI namespace. Consolidate new account or settings behavior into the same `/account` scope.
- Prefer no third-party dependencies for platform core behavior. If a dependency is unavoidable, explain the need, isolate it behind an interface, and make its replacement possible.

Every phase:

1. Confirm `make test` is green before implementation.
2. Read the focused source and test files before creating a new design.
3. Keep one phase limited to one verifiable capability.
4. Change related code, API validation, Web behavior, persistence, service/search behavior, unit/integration tests, and documentation together when that behavior crosses layers.
5. Record API, behavior, environment, and next actions in `README.md`.
6. Verify with `make unit`, then `make integration`, then `make test`.
7. Review the focused diff and produce one local commit named `Phase NN: <short Chinese summary>`.
8. Do not commit generated files; clean runtime artifacts before staging.
9. Return to this file before the next phase.

Failure handling:

- A phase is not complete while `make test`, `git status --short`, or `git diff --check` fails.
- On a failure, diagnose the root cause first and keep the first change focused on that cause.
- Do not suppress or weaken a failing test until it is proven to encode the wrong requirement.
- After three related failures, record the exact blocked step, observed error, likely cause, smallest diagnostic step, and next action in `README.md`; do not continue to a later phase.

## Current Priorities

Continue through the fine-grained sequence in `PLAN.md`. Keep follow-up work divided
into independently reviewable phases using `Phase NN` numbering from Phase 09 onward.

## Ending Sweep

1. Run `make test` from a clean workspace.
2. Inspect `/`, `/login`, category, article, and search flows with `make run`.
3. Confirm Chinese UI copy and signed or unsigned path handling.
4. Confirm `make test` still passes when the current working directory is another writable location.
5. Record environment setup, commands, test evidence, known limitations, and next phases in `README.md`.
