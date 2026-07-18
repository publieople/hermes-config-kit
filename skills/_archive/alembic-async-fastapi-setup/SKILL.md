---
name: alembic-async-fastapi-setup
description: Set up Alembic database migrations for FastAPI projects using async SQLAlchemy (asyncpg). Covers env.py configuration with async engine, autogenerate handling, greenfield vs brownfield migration strategies, and env var integration.
---

# Alembic Async FastAPI Setup

Set up database migrations for FastAPI projects using async SQLAlchemy 2.0 + asyncpg.

## When to Use
- Starting a new FastAPI project with async PostgreSQL
- Configuring Alembic with `create_async_engine` instead of sync `engine_from_config`
- Writing initial migrations for greenfield (new database) vs brownfield (existing database)

## Installation

Alembic comes as a dependency of SQLAlchemy, but verify:

```bash
alembic --version
```

## Initialization

```bash
alembic init alembic
```

This creates:
- `alembic/` directory with `env.py`, `script.py.mako`, `versions/`
- `alembic.ini` at project root

## Configure alembic.ini

Set the database URL as a fallback (the env.py will prefer env var):

```ini
sqlalchemy.url = postgresql+asyncpg://postgres:postgres@localhost:5432/mydb
```

## Configure env.py for async

Replace the generated `env.py` with this async setup:

```python
"""
Alembic migration environment — async SQLAlchemy support.
"""
import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.models import Base  # your models' Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Priority: env var > alembic.ini fallback
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    config.get_main_option("sqlalchemy.url", "postgresql+asyncpg://postgres:postgres@localhost:5432/mydb"),
)


def run_migrations_offline():
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online():
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

Key differences from default:
- Uses `create_async_engine` instead of `engine_from_config`
- Wraps sync migration ops in `connection.run_sync()`
- Runs via `asyncio.run()`

## Generating Migrations

### Autogenerate (brownfield — DB already exists)

```bash
DATABASE_URL="postgresql+asyncpg://..." alembic revision --autogenerate -m "description"
```

**Pitfall:** Autogenerate compares models against the existing database. It produces `ALTER TABLE` statements for brownfield, which is correct. But for greenfield, it will also produce ALTER TABLE if there's already a schema — you want `CREATE TABLE` instead.

### Manual migration (greenfield — new database)

For a fresh project with no existing database, write `CREATE TABLE` statements manually in the migration:

```python
def upgrade():
    op.create_table(
        "my_table",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_my_table_id", "my_table", ["id"])
```

**When to choose manual over autogenerate:**
- Greenfield project (no existing DB to compare against)
- Autogenerate produces ALTER TABLE when you need CREATE TABLE
- You want full control over the generated SQL

## Applying Migrations

```bash
# Apply all pending
alembic upgrade head

# Check current state
alembic current

# View history
alembic history

# Rollback one step
alembic downgrade -1
```

## Integration with Scripts

For a `setup_db.py` bootstrap script:

```python
import subprocess, sys

def run_migrations():
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"Migration failed: {result.stderr}")
        sys.exit(1)
```

## Common Pitfalls

- **env.py module import fails** — ensure your package is installed or PYTHONPATH includes `src/`
- **Autogenerate produces ALTER TABLE for new project** — the tool compared against an existing DB. Delete the migration, drop the old DB, and regenerate.
- **ImportError for async engine** — ensure `sqlalchemy[asyncio]` extra is installed
- **Windows + asyncpg** — asyncpg requires native compilation. For Windows dev, consider using sync mode for Alembic (revert to sync `engine_from_config`) or use WSL.
