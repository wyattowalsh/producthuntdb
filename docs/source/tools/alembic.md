# Alembic - Database Migrations

::::{grid} 2
:gutter: 3

:::{grid-item}
**Category:** Migrations  
**Official Site:** [alembic.sqlalchemy.org](https://alembic.sqlalchemy.org/)  
**GitHub:** [sqlalchemy/alembic](https://github.com/sqlalchemy/alembic)  
**License:** MIT
:::

:::{grid-item}
**Version:** Latest  
**Used For:** Schema migrations, version control for database changes  
**Why We Use It:** Mature, battle-tested migration tool built on SQLAlchemy
:::

::::

---

## Overview

Alembic is the standard migration tool for SQLAlchemy-based projects. It provides a revision history, autogeneration of schema diffs, and a small but powerful command set for upgrading/downgrading databases.

## How ProductHuntDB Uses Alembic

- Track schema changes in `alembic/versions/`.
- Autogenerate migrations from model changes and commit revisions.
- Apply migrations during CI and in `producthuntdb migrate` / `producthuntdb upgrade` flows.

### Common Commands

```bash
# Create an autogenerate revision
alembic revision --autogenerate -m "describe change"

# Upgrade to latest
alembic upgrade head

# Downgrade one revision
alembic downgrade -1

# Show current revision
alembic current
```

### Integration Notes

- Ensure SQLModel/SQLAlchemy metadata is importable by Alembic (adjust `env.py` to import the models).
- Review autogenerate diffs carefully — complex changes often require hand-editing.

## Best Practices

- Commit migration files (versioned) to source control.
- Keep migrations minimal and reversible when possible.
- Use CI to validate migrations against a fresh DB.

## Learn More

- 📚 [Official Alembic Docs](https://alembic.sqlalchemy.org/en/latest/)
- 🐛 [Issue Tracker](https://github.com/sqlalchemy/alembic/issues)

:::{seealso}
See [SQLModel](sqlmodel) for how models feed into migrations.
:::

