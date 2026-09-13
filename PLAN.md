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

- The crawl map supports exactly 5 million deterministic URLs from 1 to 5,000,000 inclusive.
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

## Phase 20 — Login Experience and Source Status

Scope: make the login page usable with Chinese labels and explicit failure feedback, redirect signed-in visitors
to the dashboard, and expose the already registered built-in and RSS connectors through `/api/sources`.

Acceptance:

- The login form presents Chinese field labels and keeps invalid submissions at HTTP 401.
- An authenticated visitor opening `/login` is redirected to `/` without replacing the existing session.
- `/api/sources` reports each service connector, article count, category counts, and ingestion diagnostics.
- No new dependency is introduced; RSS remains configured through `PLATFORM_FEEDS`.

## Phase 21 — Frontend and Backend Separation

Scope: split the browser experience into static HTML/CSS/JavaScript in `frontend/`, move pages onto the
existing service-backed JSON API, and keep the Python process only as an API/static-file provider.

Acceptance:

- `/` and all main routes serve `frontend/index.html` and load `/static/app.js` and `/static/styles.css`.
- Login, categories, articles, search, and source diagnostics are accessible as JSON APIs.
- Signed and unsigned `/account` paths serve the application shell without creating a second account namespace.
- Static loader blocks paths outside `frontend/`.
- The same category, article, search, and source data remain protected by CLI-backed service methods.
- There is no npm/Node/Vite/React build dependency; the front end uses standard browser platform APIs.

## Phase 22 — Editorial UI Refinement

Scope: align the separated UI with mainstream news patterns while keeping it a static shell and
JSON-only backend. Prioritize clear typography, stable category navigation, article-first hierarchy,
responsive cards, and calm neutral tokens.

Acceptance:

- The page shell uses a compact masthead, rounded search, and horizontally scrollable categories.
- Article cards show a semantic layout with title, summary, tags, date/source/category, and read link.
- Login and account views avoid distraction and keep localized copy.
- Light and dark schemes use consistent color, spacing, radius, and hover cues.
- No build tool or new dependency is introduced.

## Phase 27 — 宽屏、平板和移动端适配

Scope: 调整前端单壳的版面宽度、分区行为、卡片栏数和紧凑内边距，使宽屏不过度拉伸，平板和手机避免横向溢出。

Acceptance:

- 分类导航在前台所有断点保持横向主导航，不使用标签胶囊。
- 1240px 以上版面继续使用宽屏内容宽度，但设置最大宽度上限。
- 1120px 以下允许顶部操作折行，880px 以下内容和来源进入单列。
- 420px 和 360px 宽度使用紧凑边距并保持表单、正文和页脚可读。
- 来源渲染可以容忍 bootstrap 来源缺少分类数组，避免前端进入错误状态。
- 不引入新的前端依赖。

## Phase 28 — 手动信息源接入

Scope: 在现有 RSS 连接器协议上增加登录后的来源管理动作，把 RSS 地址写入可配置的服务端来源，并立即读取最近内容。

Acceptance:

- 登录后可以在 `/sources` 页面添加来源名称、分类、RSS 地址和条目上限。
- 后端会读取 RSS 内容、保存文章、更新来源列表和内存搜索索引。
- 来源 slug 自动规范为 ASCII，重复添加会被拒绝。
- 拉取失败、非法 URL、非法分类和超出条目上限都以中文错误报告。
- 不新增第三方依赖，也不允许未登录用户修改来源。
