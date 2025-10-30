# CLI Reference

ProductHuntDB exposes a Typer-powered CLI (`uv run producthuntdb`) with subcommands for initialization, synchronization, export, and publishing workflows. All commands inherit global options such as `--verbose` for expanded logging.

## Core Operations

### `sync`

Synchronize Product Hunt data into the SQLite store.

```bash
uv run producthuntdb sync [OPTIONS]
```

| Option | Description |
| --- | --- |
| `--full-refresh`, `-f` | Rebuild the database from scratch, ignoring incremental cursors. |
| `--max-pages`, `-n INTEGER` | Limit pagination depth per entity (useful for smoke tests). |
| `--posts-only` | Skip auxiliary entities (topics, collections) to focus on launches. |
| `--verbose`, `-v` | Emit detailed GraphQL payloads and rate-limit headers. |

### `export`

Generate CSV exports (and optionally a SQLite snapshot).

```bash
uv run producthuntdb export [OPTIONS]
```

| Option | Description |
| --- | --- |
| `--output-dir`, `-o PATH` | Destination directory (default: `export/` under the repo root). |
| `--include-db / --no-include-db` | Control inclusion of a `.db` copy alongside CSV files. |

### `publish`

Upload the latest export bundle to Kaggle.

```bash
uv run producthuntdb publish [OPTIONS]
```

| Option | Description |
| --- | --- |
| `--force` | Perform a live publish (default is dry-run validation). |
| `--notes TEXT` | Release notes appended to the Kaggle version. |
| `--verbose`, `-v` | Show HTTP responses from the Kaggle API. |

### `status`

Summarize database health, row counts, file sizes, and last-sync timestamps.

```bash
uv run producthuntdb status
```

### `verify`

Smoke-test API credentials and rate-limit status.

```bash
uv run producthuntdb verify [--verbose]
```

## Database Lifecycle

| Command | Purpose |
| --- | --- |
| `uv run producthuntdb init` | Initialize directories, migrations, and the default schema. |
| `uv run producthuntdb migrate --message "..."` | Autogenerate Alembic migrations after model changes. |
| `uv run producthuntdb upgrade [REVISION]` | Apply migrations up to a target revision (defaults to `head`). |
| `uv run producthuntdb downgrade [REVISION]` | Roll back to a previous revision. |
| `uv run producthuntdb migration-history` | View revision history with timestamps. |

## Command Completion

Enable shell completions for faster navigation:

```bash
uv run producthuntdb --install-completion zsh
source ~/.zfunc/_producthuntdb
```

Refer to Typer's documentation for additional shells.

## Logging & Exit Codes

- All commands log to stdout and `logs/producthuntdb.log`.
- Non-zero exit codes signal operational failures (useful for CI/CD workflows).
