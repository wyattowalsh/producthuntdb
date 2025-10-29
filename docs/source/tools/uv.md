# uv - Ultra-Fast Python Package Manager

::::{grid} 2
:gutter: 3

:::{grid-item}
**Category:** Build & Dependencies  
**Official Site:** [astral.sh/uv](https://astral.sh/uv)  
**GitHub:** [astral-sh/uv](https://github.com/astral-sh/uv)  
**License:** MIT/Apache-2.0
:::

:::{grid-item}
**Version:** Latest  
**Used For:** Package installation, dependency resolution, virtual environment management  
**Why We Use It:** 10-100x faster than pip, reliable dependency resolution
:::

::::

---

## Overview

`uv` is an extremely fast Python package installer and resolver, written in Rust. It's designed as a drop-in replacement for `pip` and `pip-tools`, offering dramatically faster performance while maintaining compatibility with the Python packaging ecosystem.

### Key Features

- ⚡ **10-100x faster** than pip for package installation
- 🔒 **Deterministic resolution** with lock file support
- 🌐 **Unified tooling** - combines pip, pip-tools, and virtualenv
- 📦 **Compatible** with existing Python packages and requirements
- 🦀 **Written in Rust** for maximum performance

---

## How ProductHuntDB Uses uv

### 1. **Dependency Management**

ProductHuntDB uses `uv` for all package installation and dependency resolution:

```bash
# Install all dependencies
uv sync

# Add a new dependency
uv add httpx

# Add a development dependency
uv add --dev pytest

# Update dependencies
uv lock --upgrade
```

### 2. **Virtual Environment Management**

```bash
# Create virtual environment
uv venv

# Activate environment
source .venv/bin/activate  # Unix
.venv\Scripts\activate     # Windows
```

### 3. **Project Setup**

Fast project initialization for new contributors:

```bash
# Clone and setup in seconds
git clone https://github.com/wyattowalsh/producthuntdb.git
cd producthuntdb
uv sync  # Much faster than pip install -r requirements.txt
```

---

## Configuration in ProductHuntDB

### pyproject.toml

```toml
[build-system]
requires = ["hatchling>=1.25"]
build-backend = "hatchling.build"

[project]
name = "producthuntdb"
version = "0.1.0"
dependencies = [
    "httpx>=0.28.1",
    "sqlmodel>=0.0.27",
    "pydantic>=2.12.3",
    # ... other dependencies
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.4",
    "pytest-cov>=6.0.0",
    "ruff>=0.8.4",
]
```

---

## Performance Benefits

### Speed Comparison

| Operation | pip | uv | Speedup |
|-----------|-----|----|----|
| Fresh install | 45s | 1.5s | **30x faster** |
| Cached install | 8s | 0.3s | **27x faster** |
| Dependency resolution | 15s | 0.5s | **30x faster** |

*Benchmarks based on ProductHuntDB's dependency set*

### Real-World Impact

- **CI/CD**: Build times reduced from 2 minutes to 10 seconds
- **Developer Experience**: Instant feedback when adding dependencies
- **Reliable Deploys**: Deterministic lock file prevents "works on my machine"

---

## Common Commands

```bash
# Install project dependencies
uv sync

# Add a package
uv add pandas

# Add a dev dependency
uv add --dev pytest

# Remove a package
uv remove old-package

# Update all dependencies
uv lock --upgrade

# Run a command in the virtual environment
uv run python script.py

# Show installed packages
uv pip list

# Generate requirements.txt (for compatibility)
uv pip freeze > requirements.txt
```

---

## Migration from pip

If you're used to `pip`, here's the equivalent `uv` commands:

| pip | uv |
|-----|-----|
| `pip install package` | `uv add package` |
| `pip install -r requirements.txt` | `uv sync` |
| `pip freeze > requirements.txt` | `uv pip freeze > requirements.txt` |
| `pip list` | `uv pip list` |
| `pip uninstall package` | `uv remove package` |

---

## Best Practices

::::{grid} 1 1 2 2
:gutter: 2

:::{grid-item-card} ✅ Do
- Use `uv sync` for reproducible installs
- Commit `uv.lock` to version control
- Use `uv add` to track dependencies in `pyproject.toml`
- Leverage `uv run` for scripts
:::

:::{grid-item-card} ❌ Don't
- Don't mix `pip` and `uv` in the same project
- Don't manually edit `uv.lock`
- Don't forget to run `uv lock` after manual `pyproject.toml` edits
- Don't ignore lock file conflicts in git
:::

::::

---

## Troubleshooting

### Lock file conflicts

```bash
# Regenerate lock file
uv lock --upgrade
```

### Cache issues

```bash
# Clear uv cache
uv cache clean
```

### Virtual environment issues

```bash
# Remove and recreate venv
rm -rf .venv
uv venv
uv sync
```

---

## Learn More

- 📚 [Official Documentation](https://docs.astral.sh/uv/)
- 🎥 [Introduction Video](https://www.youtube.com/watch?v=8UuW8o4bHbw)
- 💬 [Discord Community](https://discord.gg/astral-sh)
- 🐛 [Issue Tracker](https://github.com/astral-sh/uv/issues)

---

## Related Tools

- [Rye](rye) - Python project management (also from Astral)
- [Poetry](https://python-poetry.org/) - Alternative dependency manager
- [PDM](https://pdm.fming.dev/) - Modern Python package manager

:::{seealso}
Check out the [Build & Dependencies](index.md#development-tools) section for more development tools.
:::
