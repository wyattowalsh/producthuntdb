# Kaggle API - Dataset Publishing

::::{grid} 2
:gutter: 3

:::{grid-item}
**Category:** Dataset Publishing  
**Official Site:** [kaggle.com/docs/api](https://www.kaggle.com/docs/api)  
**GitHub:** [Kaggle/kaggle-api](https://github.com/Kaggle/kaggle-api)  
**License:** Apache-2.0
:::

:::{grid-item}
**Version:** ≥1.7.4.5  
**Used For:** Dataset uploads, version management, metadata updates  
**Why We Use It:** Official API for automated Kaggle datasets
:::

::::

---

## Overview

The Kaggle API provides a command-line interface and Python library for interacting with Kaggle datasets, competitions, and kernels programmatically.

### Key Features

- 📦 **Dataset Management** - Create, update, download datasets
- 🔄 **Version Control** - Track dataset versions automatically
- 📊 **Metadata** - Rich metadata with schema definitions
- 🤖 **Automation** - Perfect for CI/CD pipelines
- 🌐 **Public/Private** - Control dataset visibility
- 📈 **Analytics** - Track views and downloads

---

## How ProductHuntDB Uses Kaggle

### 1. **Automated Publishing**

Publish database and CSV exports to Kaggle:

```python
from kaggle.api.kaggle_api_extended import KaggleApi
from producthuntdb.config import settings

def publish_to_kaggle():
    """Publish dataset to Kaggle."""
    api = KaggleApi()
    api.authenticate()
    
    # Create new version
    api.dataset_create_version(
        folder="data/export",
        version_notes="Updated with latest Product Hunt data",
        quiet=False,
    )
```

### 2. **CLI Integration**

Built into ProductHuntDB CLI:

```bash
# Publish dataset
producthuntdb publish

# With custom message
producthuntdb publish --message "Added 1000 new posts"
```

### 3. **Dataset Metadata**

Comprehensive dataset information:

```json
{
  "title": "Product Hunt Database",
  "id": "wyattowalsh/product-hunt-database",
  "licenses": [{"name": "MIT"}],
  "keywords": ["product-hunt", "startups", "products"],
  "collaborators": [],
  "data": [
    {
      "path": "producthunt.db",
      "description": "SQLite database with all Product Hunt data"
    },
    {
      "path": "posts.csv",
      "description": "All Product Hunt posts"
    }
  ]
}
```

---

## Configuration in ProductHuntDB

### API Authentication

```python
# ~/.kaggle/kaggle.json
{
  "username": "your_username",
  "key": "your_api_key"
}

# Or via environment variables
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_api_key
```

### Dataset Metadata

```python
# data/dataset-metadata.json
{
  "title": "Product Hunt Database",
  "id": "wyattowalsh/product-hunt-database",
  "subtitle": "Complete Product Hunt data pipeline",
  "description": "Production-grade SQLite database...",
  "isPrivate": false,
  "licenses": [{"name": "MIT"}],
  "keywords": [
    "product-hunt",
    "startups", 
    "products",
    "sqlite",
    "dataset"
  ],
  "collaborators": [],
  "data": []
}
```

---

## Common Commands

```bash
# List your datasets
kaggle datasets list --mine

# Download a dataset
kaggle datasets download -d wyattowalsh/product-hunt-database

# Create new dataset
kaggle datasets create -p /path/to/dataset

# Update existing dataset (new version)
kaggle datasets version -p /path/to/dataset -m "Update message"

# View dataset metadata
kaggle datasets metadata -d wyattowalsh/product-hunt-database

# Get dataset status
kaggle datasets status -d wyattowalsh/product-hunt-database
```

---

## Python API Usage

### Publishing Updates

```python
from kaggle.api.kaggle_api_extended import KaggleApi

def update_dataset(folder_path: str, message: str):
    """Create new dataset version."""
    api = KaggleApi()
    api.authenticate()
    
    # Upload new version
    api.dataset_create_version(
        folder=folder_path,
        version_notes=message,
        convert_to_csv=False,
        delete_old_versions=False,
    )
```

### Downloading Datasets

```python
def download_dataset(dataset: str, path: str = "."):
    """Download a Kaggle dataset."""
    api = KaggleApi()
    api.authenticate()
    
    api.dataset_download_files(
        dataset=dataset,
        path=path,
        unzip=True,
    )
```

### Checking Status

```python
def get_dataset_info(dataset: str) -> dict:
    """Get dataset metadata."""
    api = KaggleApi()
    api.authenticate()
    
    return api.dataset_metadata(dataset)
```

---

## Best Practices

::::{grid} 1 1 2 2
:gutter: 2

:::{grid-item-card} ✅ Do

- Include comprehensive metadata
- Write clear version notes
- Provide schema documentation
- Test locally before publishing
- Use semantic versioning

:::

:::{grid-item-card} ❌ Don't

- Don't commit API credentials
- Don't publish untested data
- Don't skip version notes
- Don't upload without metadata
- Don't forget file descriptions

:::

::::

---

## Learn More

- 📚 [Official Documentation](https://www.kaggle.com/docs/api)
- 🎓 [Getting Started](https://github.com/Kaggle/kaggle-api#readme)
- 🔧 [API Reference](https://www.kaggle.com/docs/api#api-reference)

---

## Related Tools

- [Pandas](pandas) - CSV file generation
- [SQLite](sqlite) - Database export

:::{seealso}
See the [CLI Reference](../index.md#cli-reference) for the `producthuntdb publish` command.
:::
