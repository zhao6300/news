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
- An in-memory repository layer is covered and can later be replaced without business-service changes.
- Settings snapshots change without changing callers.

## Phase 03 — Storage Layer

Introduce a replaceable repository interface and an in-memory implementation.

Acceptance:

- Read operations and storage extension registration are covered.
- Storage can be swapped without business-service changes.

## Phase 04 — Service Layer

Implement category-scoped queries, creation, and status tracking.

Acceptance:

- Business rules are isolated from storage and web code.
- Account authentication is covered by in-memory session tests.
- Service behavior is covered by unit tests.

## Phase 05 — Web UI

Deliver a clean, login-gated Web interface with category navigation.

Acceptance:

- The UI communicates through the service layer, not directly with extensions.
- Category detail pages and article detail pages are covered by tests.
- The health endpoint is covered by tests.
- Keyword search is available through `/api/search` and `/search?q=`.

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

## Fine-Grained Continuation Plan

This backlog maps the already-completed Phase 01–08 baseline into smaller restartable steps.
Each phase requires green pre-phase tests, focused changes, updated tests and README, an
ending Git sweep, review of the focused diff, and one independent local commit.

## Phase 09 — Roadmap and Agent Rules

Scope: define Phase 09–18 acceptance and testing workflow in `PLAN.md` and `AGENTS.md`.

Acceptance:

- The continuation sequence has concrete UI, API, persistence, service, testing, and operational scopes.
- The rules require Chinese user-facing text, root-cause diagnosis, focused diff review, clean ending status, and one commit for each phase.

## Phase 10 — Account Identity and Ownership

Scope: extend the stable account model with display name, timezone, active status, and last-seen timestamp; keep one platform owner available to privileged routes.

Acceptance:

- Account creation rejects duplicate email addresses and validates non-empty identity fields.
- Account manager requires the first owner account and returns it for authoritative use.
- Authentication confirms the account remains active.
- Unit and integration suites cover profile defaults, duplicate prevention, and inactive login rejection.

## Phase 11 — Owner Access Key Management

Scope: add the internal owner registration and API-key verification layer used by all account routes.

Acceptance:

- Registration requires complete identity fields and rejects duplicate email addresses.
- Regenerated verification keys replace the prior key as a range-scoped value.
- Verification keys remain inactive when no owner member sends the request.
- The account route can resolve an owner by a verification key before dispatching to privileged API responses.

## Phase 12 — Account Profile Gateway

Scope: implement the authoritative `/account` and `/account/api/{action}` dispatch layer that validates a profile key before entering profile, admin, menu, or widget actions.

Acceptance:

- `/account` is the only account namespace and accepts signed or unsigned URLs.
- Failed profile verification returns 404 without leaking 403.
- Trusted profile, admin, menu, and widget handlers receive the authenticated owner.
- Dispatch behavior is covered by direct module tests without adding a second UI namespace.

## Phase 13 — Preferences and News Subscription

Scope: add a `Preferences` dataclass keyed by slug with per-model subscriptions and newsletter settings.

Acceptance:

- The model supports compact JSON defaults, cloning, default typing, and profile typing.
- Account creation initializes preferences; active membership remains the callback condition.
- Profile settings and model subscriptions are covered before HTML/API integration.

## Phase 14 — Account Data Model Upgrade

Scope: replace the primitive account dataclass with `Address` and `Profile` classes and related integers.

Acceptance:

- Address validates three lines, country, postcode, and optional phone.
- Profile validates handwriting and bibliography and supports data replacement.
- Account IDs, first names, last names are stored as integers.
- Persisted account properties, status, last-seen time, preferences, model subscriptions, and instance state are covered.

## Phase 15 — Account Settings Use-Cases

Scope: validate the upgraded account model and prepare the use-cases used by `/account/account.html` and `/account/account/{slug}.html`.

Acceptance:

- Account settings validate complete identity and profile fields.
- Public account links normalize display names into signed slot paths.
- Settings behavior is covered by module tests without changing route dispatch until the HTML phase.

## Phase 16 — Large-Scale Content Crawl

Scope: crawl 5 million URLs using a scalable crawl plan and chunk-size 2.

Acceptance:

- The crawl map supports 5 million deterministic URLs.
- The crawl component supports name, description, plan, amount, and protected saver interface.
- Setting `amount` fails when unsupported by the crawl type.
- Google and Bing adapters implement caching and NoCcache behavior where required.
- Initialization and API behavior are covered in tests.

## Phase 17 — Crawler-to-Platform Integration

Scope: feed crawled sources into the existing storage, service, and content pipeline.

Acceptance:

- Downloaded JSON uses content, type, and writer fields.
- Workflows generate a cache summary, stats, map, and a JSON crawl report.
- Serializing, loading, and batching crawl results are covered for normal and invalid content.
- Public load/save URLs are protected by an owner gate.

## Phase 18 — Search Fusion and Platform Finalization

Scope: have every search tool use the shared completed search fusion and finish cross-platform behavior.

Acceptance:

- Website search and API search run through the same compatible search-fusion rules.
- Platform can run inside an account environment and use direct inspect, direct search, and an account menu.
- Search provides responsive page behavior and can load image results supplied through URL queries.
- The final phase records environment setup, commands, test evidence, known limitations, and next actions.
