# Development Plan

## Phase 01 — Project Skeleton

Deliver a clean repository with `README.md`, `AGENTS.md`, `PLAN.md`, `Makefile`, `src/`, and `tests/`.

Acceptance:

- `make test` passes.
- The workspace can run the placeholder application with `make run`.

## Phase 02 — Domain Typing and Configuration

Add stable data models and settings loading for the information categories.

Acceptance:

- Categories and records are validated.
- Settings snapshots change without changing callers.

## Phase 03 — Storage Layer

Introduce a replaceable repository interface and an in-memory implementation.

Acceptance:

- Read operations and storage extension registration are covered.
- Storage can be swapped without business-service changes.
- Storage can be swapped without business-service changes.

## Phase 04 — Service Layer

Implement category-scoped queries, creation, and status tracking.

Acceptance:

- Business rules are isolated from storage and web code.
- Service behavior is covered by unit tests.

## Phase 05 — Web UI

Deliver a clean, login-gated Web interface with category navigation.

Acceptance:

- The UI communicates through the service layer, not directly with extensions.
- The health endpoint is covered by tests.

## Phase 06 — Test Coverage

Expand service, storage, and HTTP integration coverage.

Acceptance:

- Fast unit and integration layers are available.
- `make test` runs both layers without long start time.

## Phase 07 — Extensibility Baseline

Prepare a source-connector interface and performance baseline.

Acceptance:

- A new source can be added through registration without changing service internals.
- Pagination behavior is covered.

## Phase 08 — Documentation and Operations

Document setup, architecture, category model, and next phases.

Acceptance:

- `README.md` explains run/test workflows.
- Known issues and next actions are explicit.
