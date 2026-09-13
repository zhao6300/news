# Agent Rules

- Keep every implementation phase independently testable and narrowly scoped.
- Run `make test` before starting a new phase.
- Do not introduce dependencies without explaining the reason.
- Stop expanding a phase after three related test failures; record the next actionable step.
- Every successful phase must produce a focused local commit.
