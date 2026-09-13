# News Intelligence Platform

A phased build for a modular AI information platform covering news, technology, models, reviews, and related categories.

## What is here

- `src/app.py` — browser routes and HTML rendering.
- `src/auth.py` — account-model login flow.
- `src/connectors.py` — extension protocol for new information sources.
- `src/extensions/builtin.py` — seeded content for the initial platform schema.
- `src/services.py` — service-layer access to extensions.
- `tests/` — focused unit and HTTP integration tests.

## Requirements

- Python 3.11+
- Make

## Commands

```bash
make test
make run
```

## Web experience

The platform provides a clean home view, extension-linked navigation, category listings, a login screen, and a health endpoint. The built-in demo account accepts `member@example.com` and `demo-password` for early development only.

## How to inspect

```bash
make test
make run
```

## Built-in extensions

The platform exposes `AI`, `Technology`, `Models`, and `Reviews` as first-class extension categories so new sources can be added without changing downstream services.

## Web endpoints

- `/` — home dashboard with all extension entries.
- `/extensions/{slug}` — category listing.
- `/login` — early development login form.
- `/health` — process status check.

## Known next steps

1. Move seeded content into a persistent storage-backed repository.
2. Replace the placeholder password store with settings-backed account records and real session cookies.
3. Add source scheduling and ingestion diagnostics.
4. Expand category navigation and article detail pages.
