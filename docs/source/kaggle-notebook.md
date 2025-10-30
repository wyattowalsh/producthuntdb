# Kaggle Notebook Guide

The ProductHuntDB Kaggle notebook (`notebooks/ProductHuntDB Notebook.ipynb`) provides a complete, production-ready workflow for managing Product Hunt datasets on Kaggle.

## Features

- **Clean, minimal design** with styled header banner
- **CLI-based workflow** using `producthuntdb` commands
- **Smart installation** that detects Kaggle vs local environments
- **Data analysis & visualizations** with pandas and seaborn
- **Automatic export & publishing** to Kaggle datasets
- **Complete documentation** and troubleshooting guide

## Quick Start

1. **Upload** the notebook to Kaggle
2. **Configure Secrets** in Notebook Settings → Add-ons → Secrets:
   - `PRODUCTHUNT_TOKEN` (required) - Get from [api.producthunt.com](https://api.producthunt.com/v2/oauth/applications)
   - `KAGGLE_USERNAME`, `KAGGLE_KEY`, `KAGGLE_DATASET_SLUG` (optional, for publishing)
3. **Run all cells** to install, sync, analyze, and publish
4. **Schedule** the notebook for automatic updates

## Workflow

The notebook follows this workflow using CLI commands:

```bash
# 1. Install and configure
pip install git+https://github.com/wyattowalsh/producthuntdb.git

# 2. Initialize database
producthuntdb init

# 3. Verify authentication
producthuntdb verify

# 4. Sync data
producthuntdb sync --max-pages 10  # Limited for testing
producthuntdb sync --full-refresh  # Full historical data
producthuntdb sync                 # Incremental update

# 5. Check status
producthuntdb status

# 6. Export to CSV
producthuntdb export

# 7. Publish to Kaggle
producthuntdb publish
```

## Notebook Structure

1. **Header** - Styled banner with project branding
2. **Overview** - Introduction and key features
3. **Installation** - Smart environment detection and setup
4. **Configuration** - Kaggle Secrets setup guide
5. **Database Init** - Initialize and verify connections
6. **Data Sync** - Fetch data from Product Hunt API
7. **Statistics** - View database status and metrics
8. **Analysis** - SQL queries and data exploration
9. **Visualizations** - Charts and trend analysis
10. **Export** - Generate CSV files
11. **Publishing** - Upload to Kaggle datasets
12. **Scheduling** - Guide for automated updates
13. **Reference** - Complete CLI command reference
14. **Troubleshooting** - Common issues and solutions

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
   - Run full refresh once: `producthuntdb sync --full-refresh`
   - Test with limited pages first: `producthuntdb sync --max-pages 10`

2. **Regular Updates**
   - Use incremental sync: `producthuntdb sync`
   - Schedule notebook to run daily or weekly
   - Monitor execution logs for errors

3. **Security**
   - Always use Kaggle Secrets for credentials
   - Never commit tokens to version control
   - Regularly rotate API keys

4. **Performance**
   - Limit concurrent requests with `MAX_CONCURRENCY` env var
   - Use appropriate `PAGE_SIZE` for your needs
   - Monitor rate limits and adjust accordingly

## Troubleshooting

### Installation Issues

```bash
# Reinstall the package
!pip uninstall -y producthuntdb
!pip install -q git+https://github.com/wyattowalsh/producthuntdb.git
```

### Database Issues

```bash
# Reset database (WARNING: deletes all data)
!rm -f /kaggle/working/producthunt.db*
!producthuntdb init
```

### API Rate Limiting

- Reduce `--max-pages` for testing
- Use incremental updates instead of full refresh
- Verify token: `producthuntdb verify`

## Example Output

The notebook produces:

- **SQLite Database** - Normalized schema with indexes
- **CSV Exports** - One file per table
- **Kaggle Dataset** - Automatically versioned and published
- **Visualizations** - Charts and statistical analysis
- **Logs** - Detailed execution logs

## Resources

- [GitHub Repository](https://github.com/wyattowalsh/producthuntdb)
- [Product Hunt API Docs](https://api.producthunt.com/v2/docs)
- [CLI Reference](cli-reference.md)
- [Configuration Guide](configuration.md)
