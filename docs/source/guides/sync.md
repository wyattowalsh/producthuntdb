# Nightly Sync Playbook

This guide covers the recommended flow for keeping your local ProductHuntDB mirror in sync with Product Hunt's GraphQL API.

## Prerequisites

- Valid `PRODUCTHUNT_TOKEN` loaded via `.env` or environment variables.
- Database initialized with `uv run producthuntdb init`.
- Outbound network connectivity to `https://api.producthunt.com`.

## Incremental Sync

```bash
# Run from the project root
uv run producthuntdb sync
```

The default mode performs an incremental pull with a five-minute safety margin to avoid missed posts. The gap is configurable via `Settings.safety_minutes`.

Expected output:

- Upserted counts for posts, users, topics, collections, and related link tables.
- Rate-limit status plus request timings in the log stream.

## Full Refresh (Disaster Recovery)

```bash
uv run producthuntdb sync --full-refresh
```

Use this when restoring from backups or rebuilding the SQLite database from scratch. The process iterates through every entity and can take 30+ minutes depending on connection limits.

## Shaping the Sync

- `--max-pages`: throttle API usage during smoke tests.
- `--posts-only`: focus on launches when triaging incidents.
- `--verbose`: surface GraphQL payloads when debugging.

## Scheduling

1. Create a shell wrapper (for example, `scripts/sync-nightly.sh`) that activates the repository and logs output to `logs/sync.log`.
2. Schedule via `cron` or a task runner such as `systemd` or GitHub Actions (self-hosted) to execute the wrapper nightly.
3. Monitor exit codes; a non-zero status should trigger alerting.

```cron
# Run at 01:30 UTC
30 1 * * * cd /opt/producthuntdb && /usr/bin/env UV_CACHE_DIR=/opt/uv-cache uv run producthuntdb sync >> logs/sync.log 2>&1
```

## Post-run Validation

- `uv run producthuntdb status` to confirm entity counts and storage usage.
- Inspect `logs/producthuntdb.log` for `ERROR` or `WARNING` entries.
- Check the most recent `synced_at` timestamp inside `data/producthunt.db` (see the data model reference for table names).

## Troubleshooting

If the command fails, consult the [Troubleshooting guide](troubleshooting) for known error signatures and recovery steps.
