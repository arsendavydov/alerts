# Alerts Service - FastAPI backend for monitoring alerts

Production-style backend service for centralized alert management: search, subscriptions, pauses, screenshots/links, and integrations.

## For Recruiters / Hiring Managers

This repository demonstrates:
- real backend engineering in a monitoring domain (not a toy CRUD),
- async architecture on FastAPI + PostgreSQL,
- clear layered design (`Router -> Service -> Repository`),
- business workflows around alert lifecycle and subscriptions,
- test coverage across unit/integration/e2e layers.

If you have 2-3 minutes, check:
- `fastapi/app/` - application code
- `fastapi/tests/` - test structure
- `PRD.md` - product/business requirements

## Key Features

- Alert search and filtering (with pagination and sorting)
- Alert subscriptions management (users/channels/settings)
- Alert pauses management (conditional and unconditional)
- Alert details create/update flow
- Integrations with external entities (screenshots, links, DT-related fields)
- Structured error handling and response schemas

## Tech Stack

- Python 3.10
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0 (async)
- Pydantic
- Uvicorn
- AppDynamics (monitoring integration in project context)

## Architecture

The service follows a layered architecture:

- `routers/` - HTTP endpoints and input validation
- `services/` - business logic and orchestration
- `repositories/` - data access layer (ORM/Core)
- `models/` - SQLAlchemy ORM models
- `schemas/` - pydantic request/response models
- `utils/` - db/logging/errors/context helpers
- `contracts/` - protocol-based interfaces

See also:
- `fastapi/app/ARCHITECTURE_NOTES.md`
- `PRD.md`

## Project Structure

```text
alerts/
├── PRD.md
├── README.md
└── fastapi/
    ├── app/
    │   ├── routers/
    │   ├── services/
    │   ├── repositories/
    │   ├── models/
    │   ├── schemas/
    │   ├── contracts/
    │   └── utils/
    ├── tests/
    │   ├── unit/
    │   ├── integration/
    │   └── e2e/
    └── README.md
```

## Quick Start

From project root:

```bash
pip install -r fastapi/requirements.txt
# configure env vars: db_host, db, db_login, db_password
python3.10 -m uvicorn --app-dir fastapi/app alerts:app --host 0.0.0.0 --port 8888
```

API docs:
- [http://localhost:8888/alerts/docs](http://localhost:8888/alerts/docs)

## Notes

- This is a real-world style service with domain complexity and integrations.
- Some domain names/fields are preserved from production context of monitoring workflows.
- The repository is intentionally complete to show architecture and engineering depth, not only demo endpoints.
