# Kaggle Notebook Guide

The ProductHuntDB Kaggle notebook (`notebooks/ProductHuntDB Notebook.ipynb`) provides a **streamlined, production-ready workflow** for initializing and updating Product Hunt datasets on Kaggle with automated daily updates.

## ✨ Core Features

### 🛡️ Production Reliability

- **Comprehensive error handling** - All code cells protected with try-except blocks and graceful failure modes
- **Runtime estimates** - Expected duration displayed for each cell operation
- **Progress tracking** - Sync history monitoring and checkpointing
- **Timeout resilience** - Handles Kaggle's 12-hour limit with proper timeout handling
- **Smart configuration** - Enhanced secret validation and debugging

### 📊 Dataset Management

- **Full historical harvest** - Initial data extraction with `--full-refresh` flag
- **Incremental updates** - Fast daily syncs (3-5 minutes) for new data only
- **CSV export** - Universal format for analysis and visualization
- **Kaggle dataset publishing** - Automated versioning and updates

### 🚀 Automation & Scheduling

- **Kaggle Scheduler integration** - Set-and-forget daily updates
- **Progress monitoring** - Sync history tracking to `sync_history.txt`
- **Error recovery** - Detailed troubleshooting guidance for common issues
- **Configuration validation** - Pre-flight checks before pipeline runs

## Quick Start

1. **Upload** the notebook to Kaggle
2. **Configure Secrets** in Notebook Settings → Add-ons → Secrets:
   - `PRODUCTHUNT_TOKEN` (required) - Get from [api.producthunt.com](https://api.producthunt.com/v2/oauth/applications)
   - `KAGGLE_USERNAME`, `KAGGLE_KEY`, `KAGGLE_DATASET_SLUG` (optional, for publishing)
3. **First Run**: Uncomment `--full-refresh` in sync cell (2-4 hours)
4. **Run all cells** to install, sync, and optionally publish
5. **Schedule** the notebook for automatic daily updates (re-comment `--full-refresh`)

## Workflow

The notebook executes CLI commands via subprocess:

```bash
# 1. Install and configure
pip install git+https://github.com/wyattowalsh/producthuntdb.git

# 2. Initialize database
producthuntdb init

# 3. Verify authentication
producthuntdb verify

# 4. Sync data (choose one)
producthuntdb sync --full-refresh  # First run: full historical data (2-4 hours)
producthuntdb sync                 # Daily updates: incremental only (3-5 minutes)

# 5. Check status
producthuntdb status

# 6. Export to CSV
producthuntdb export

# 7. (Optional) Publish to Kaggle
producthuntdb publish
```

## Notebook Structure (Simplified)

The notebook features **20 streamlined cells** (simplified from 32) focused exclusively on dataset initialization and daily updates:

### 1. Branding & Overview (Cells 1-3)

- **Header** - Product Hunt branded title
- **Feature overview** - Core capabilities and workflow summary
- **Production checklist** - Pre-execution validation items

### 2. Installation & Configuration (Cells 4-6)

- **Smart installation** - Auto-detects Kaggle vs local with enhanced debugging
- **Environment configuration** - Database paths and secret validation
- **Configuration guide** - Kaggle Secrets setup instructions

### 3. Database Operations (Cell 7)

- **Database initialization** - Creates SQLite database and verifies API authentication
- **Enhanced error handling** - Distinguishes between stdout/stderr properly
- **Troubleshooting** - Context-specific error messages

### 4. Data Synchronization (Cells 8-9)

- **Intelligent sync** - Full refresh (first run) or incremental (daily updates)
- **Timeout handling** - 4-hour limit with progress tracking to `sync_history.txt`
- **Status check** - Database statistics and row counts

### 5. Export & Publishing (Cells 10-11)

- **CSV export** - Universal format for analysis
- **Kaggle publishing** - Optional automated dataset updates with credential validation

### 6. Documentation (Cells 12-14)

- **Scheduling guide** - Kaggle Scheduler configuration for automated updates
- **Workflow summary** - Complete pipeline overview diagram
- **Troubleshooting** - 5 most common issues with specific solutions

## Installation Methods

### Kaggle Environment

The notebook automatically detects Kaggle and uses `pip`:

```python
pip install git+https://github.com/wyattowalsh/producthuntdb.git
```

### Local Development

For local testing with `uv`:

```bash
cd notebooks
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv sync
jupyter lab "ProductHuntDB Notebook.ipynb"
```

## Configuration

### Required Secrets

- `PRODUCTHUNT_TOKEN` - Product Hunt API token

### Optional Secrets (for publishing)

- `KAGGLE_USERNAME` - Your Kaggle username
- `KAGGLE_KEY` - Your Kaggle API key
- `KAGGLE_DATASET_SLUG` - Dataset identifier (e.g., `username/dataset-name`)

## Scheduling

To keep your dataset updated automatically:

1. Click **Notebook** → **Schedule**
2. Choose frequency (daily, weekly, etc.)
3. The notebook will run automatically and update your dataset

For scheduled runs, use incremental updates:

```python
!producthuntdb sync  # No --max-pages limit
```

This only fetches new data since the last run, making updates fast and efficient.

## Best Practices

1. **Initial Setup**
   - Run with `--full-refresh` once for complete historical data (2-4 hours)
   - Verify all secrets are configured correctly before first run

2. **Regular Updates**
   - Use incremental sync (no flags) for daily updates (3-5 minutes)
   - Schedule notebook to run daily via Kaggle Scheduler
   - Monitor `sync_history.txt` for execution tracking

3. **Security**
   - Always use Kaggle Secrets for `PRODUCTHUNT_TOKEN`
   - Never commit tokens to version control
   - Regularly rotate API keys for security

4. **Performance**
   - Incremental updates are 30-50x faster than full refresh
   - 5-minute safety margin prevents missing data between runs
   - 4-hour timeout prevents Kaggle execution limits

## Troubleshooting

### Secret Not Loading

**Problem**: `PRODUCTHUNT_TOKEN not found in Kaggle Secrets`

**Solution**:

1. Verify secret name is exactly `PRODUCTHUNT_TOKEN` (case-sensitive)
2. Check secret is added under **Notebook Settings → Add-ons → Secrets**
3. Re-run the installation cell to reload secrets
4. Check for debug output showing token length and validation errors

### Database Already Exists Warning

**Message**: `⚠️ Database already exists at /kaggle/working/data/producthunt.db`

**Status**: ✅ **This is normal and expected!**

- Kaggle notebooks persist data between runs in `/kaggle/working/`
- The database is reused across executions (this is good!)
- No action needed - just proceed to the verify step

**To force reset** (⚠️ WARNING: deletes all data):

```python
!rm -f /kaggle/working/data/producthunt.db*
!producthuntdb init --force
```

### Database Initialization Fails

**Problem**: `producthuntdb init` returns exit code 1 with SQL errors

**Solution**:

1. Check if you're using the latest version of ProductHuntDB
2. Look for specific error messages in the output
3. If you see `ProgrammingError: You can only execute one statement at a time`, update the package:

   ```python
   !pip install --upgrade git+https://github.com/wyattowalsh/producthuntdb.git
   ```

### API Authentication Failures

**Problem**: `verify` command fails even with valid token

**Solution**:

1. Check token length (minimum 10 characters required)
2. Verify token is valid at [Product Hunt API](https://api.producthunt.com/v2/oauth/applications)
3. Look for validation errors in installation cell output
4. Check `producthuntdb verify` returns exit code 0 (success)

### Sync Timeout

**Problem**: Sync exceeds 4-hour timeout

**Solution**:

- Use incremental updates (no `--full-refresh`) for daily runs
- Full refresh only needed once for initial data harvest
- Monitor `sync_history.txt` for duration tracking

### Publishing Failures

**Problem**: `kaggle publish` command fails

**Solution**:

1. Verify all three secrets configured: `KAGGLE_USERNAME`, `KAGGLE_KEY`, `KAGGLE_DATASET_SLUG`
2. Check dataset slug format: `username/dataset-name`
3. Ensure you have write permissions for the dataset
4. Verify dataset exists on Kaggle (create manually if needed)

## Example Output

The simplified notebook produces:

### Data Assets

- **SQLite Database** - Normalized schema at `/kaggle/working/data/producthunt.db`
- **CSV Exports** - Universal compatibility, one file per table in `export/` directory
- **Kaggle Dataset** - Automatically versioned and published (optional)

### Monitoring & Logs

- **Sync History** - Text log at `sync_history.txt` with timestamps and durations
- **Execution Logs** - Cell outputs with error context and troubleshooting guidance
- **Database Statistics** - Row counts and entity summaries via `producthuntdb status`

## Production Readiness

This notebook is production-ready and tested:

- ✅ **Database initialization** - Fixed SQLite "one statement at a time" error
- ✅ **Error handling** - Distinguishes normal warnings from actual errors  
- ✅ **Kaggle integration** - Automated dataset publishing with credential validation
- ✅ **Documentation** - Complete troubleshooting guide for common issues

## Resources

- [GitHub Repository](https://github.com/wyattowalsh/producthuntdb)
- [Product Hunt API Docs](https://api.producthunt.com/v2/docs)
- [CLI Reference](cli-reference.md)
- [Configuration Guide](configuration.md)
