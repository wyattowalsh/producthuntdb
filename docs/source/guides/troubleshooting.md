# Troubleshooting

This guide aggregates common operational issues and proven fixes.

## Authentication Errors

**Symptoms**

- `RuntimeError: Failed to authenticate with Product Hunt API`
- HTTP 401 responses in the log stream

**Fixes**

1. Regenerate the `PRODUCTHUNT_TOKEN` via Product Hunt developer settings.
2. Confirm `.env` is loaded: `uv run python -c "import os; print(os.getenv('PRODUCTHUNT_TOKEN') is not None)"`.
3. Retry `uv run producthuntdb verify --verbose` to confirm connectivity.

## GraphQL Rate Limits

**Symptoms**

- CLI stalls with 429 responses.
- Log messages indicating retry exhaustion.

**Fixes**

- Reduce concurrency temporarily: `PRODUCTHUNTDB_MAX_CONCURRENCY=1 uv run producthuntdb sync`.
- Schedule syncs off-peak or split entity syncs (`--posts-only` followed by topics/collections).
- Inspect the `X-RateLimit-Remaining` headers in verbose logs to refine cadence.

## Database Locked

**Symptoms**

- SQLite errors: `OperationalError: database is locked`.

**Fixes**

```bash
rm data/producthunt.db* 
uv run producthuntdb init
```

Re-run the sync once initialization completes. For automation, keep a short retention policy for WAL files.

## Export Failures

**Symptoms**

- `FileExistsError` or partial CSV output.

**Fixes**

- Pass a clean directory: `uv run producthuntdb export --output-dir export/$(date -u +%Y%m%d%H%M)`.
- Ensure the underlying filesystem has sufficient free space for the CSV bundle and (optional) SQLite snapshot.

## Kaggle Publish Errors

**Symptoms**

- HTTP 403 or invalid credentials when calling `producthuntdb publish`.

**Fixes**

- Recreate `~/.kaggle/kaggle.json` or regenerate API keys from Kaggle account settings.
- Check that `KAGGLE_DATASET_SLUG` matches the canonical `username/dataset-name`.
- Validate network access to `https://www.kaggle.com/api/v1/datasets`.

## Logging & Diagnostics

- All CLI commands log to stdout and `logs/producthuntdb.log`.
- Increase verbosity with `--verbose` to capture HTTP payloads and retry metadata.
- Wrap commands with `uv run python -m cProfile` during performance investigations.
