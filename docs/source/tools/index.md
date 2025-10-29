# Tools & Technologies

ProductHuntDB is built on a carefully selected stack of modern Python tools and technologies. Each tool was chosen for its production-grade reliability, performance, and developer experience.

::::{grid} 1 1 2 3
:gutter: 3

:::{grid-item-card} 🔧 Build & Dependencies
:link: uv
:link-type: doc

**uv** - Lightning-fast Python package installer and resolver
:::

:::{grid-item-card} 🔎 Search Tools
:link: search
:link-type: doc

**Search** - Interactive searchable & filterable tools index
:::

:::{grid-item-card} 🌐 API & HTTP
:link: httpx
:link-type: doc

**HTTPX** - Modern async HTTP client for Python
:::

:::{grid-item-card} ✅ Data Validation
:link: pydantic
:link-type: doc

**Pydantic** - Data validation using Python type hints
:::

:::{grid-item-card} 💾 Database ORM
:link: sqlmodel
:link-type: doc

**SQLModel** - SQL databases with Python objects
:::

:::{grid-item-card} 🗄️ Database Engine
:link: sqlite
:link-type: doc

**SQLite** - Self-contained SQL database engine
:::

:::{grid-item-card} 🔄 Migrations
:link: alembic
:link-type: doc

**Alembic** - Database migration tool for SQLAlchemy
:::

:::{grid-item-card} 📦 Dataset Publishing
:link: kaggle
:link-type: doc

**Kaggle API** - Automated dataset management
:::

:::{grid-item-card} 📊 Data Processing
:link: pandas
:link-type: doc

**Pandas** - Powerful data analysis library
:::

:::{grid-item-card} 🎨 CLI Interface
:link: typer
:link-type: doc

**Typer** - Modern CLI framework with type hints
:::

:::{grid-item-card} 📝 Logging
:link: loguru
:link-type: doc

**Loguru** - Simple and elegant logging
:::

:::{grid-item-card} 🔁 Retry Logic
:link: tenacity
:link-type: doc

**Tenacity** - General-purpose retrying library
:::

:::{grid-item-card} 📈 Progress Bars
:link: tqdm
:link-type: doc

**tqdm** - Fast, extensible progress bar
:::

::::

---

## Filter by Category

::::{grid} 1 1 2 2
:gutter: 2

:::{grid-item-card} 🏗️ Development Tools
:class-header: bg-primary text-white

- [uv](uv) - Package management
- [Alembic](alembic) - Database migrations
- [Typer](typer) - CLI framework
- [Loguru](loguru) - Logging
- [tqdm](tqdm) - Progress tracking
:::

:::{grid-item-card} 🗄️ Data & Storage
:class-header: bg-success text-white

- [SQLite](sqlite) - Database engine
- [SQLModel](sqlmodel) - ORM framework
- [Pandas](pandas) - Data processing
- [Kaggle API](kaggle) - Dataset publishing
:::

:::{grid-item-card} 🌐 Networking & API
:class-header: bg-info text-white

- [HTTPX](httpx) - HTTP client
- [Tenacity](tenacity) - Retry logic
- [Pydantic](pydantic) - Data validation
:::

:::{grid-item-card} ⚙️ Configuration
:class-header: bg-warning text-white

- [Pydantic Settings](pydantic) - Environment configuration
- [python-dotenv](pydantic) - .env file loading
:::

::::

---

## Quick Comparison

| Tool | Purpose | Why We Use It |
|------|---------|---------------|
| [uv](uv) | Package Management | 10-100x faster than pip, reliable dependency resolution |
| [HTTPX](httpx) | HTTP Client | Modern async support, HTTP/2, connection pooling |
| [Pydantic](pydantic) | Data Validation | Type-safe data models, automatic validation, JSON schema |
| [SQLModel](sqlmodel) | Database ORM | Combines SQLAlchemy + Pydantic, type hints everywhere |
| [SQLite](sqlite) | Database | Zero-config, single file, ACID compliant, perfect for datasets |
| [Alembic](alembic) | Migrations | Version control for database schema changes |
| [Kaggle API](kaggle) | Dataset Publishing | Official API for automated dataset updates |
| [Pandas](pandas) | Data Processing | Industry standard for CSV export and data manipulation |
| [Typer](typer) | CLI Framework | Intuitive CLI with automatic help generation |
| [Loguru](loguru) | Logging | Beautiful logging with minimal configuration |
| [Tenacity](tenacity) | Retry Logic | Robust retry strategies for API calls |
| [tqdm](tqdm) | Progress Bars | Visual feedback for long-running operations |

---

```{toctree}
:maxdepth: 1
:hidden:

uv
httpx
pydantic
sqlmodel
sqlite
alembic
kaggle
pandas
typer
loguru
tenacity
tqdm
```
