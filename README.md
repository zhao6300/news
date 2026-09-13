# News Intelligence Platform

A phased build for a clean, extensible Web platform that organizes AI, news, technology, models, and reviews.

## Requirements

- Python 3.11+
- Make

## Commands

```bash
make test
make run
```

The project starts with a verified skeleton, then adds content taxonomy, storage, services, web UI, and documentation in bounded phases.

## Built-in extensions

The platform exposes `AI`, `Technology`, `Models`, and `Reviews` as first-class extension categories so new sources can be added without changing downstream services.
