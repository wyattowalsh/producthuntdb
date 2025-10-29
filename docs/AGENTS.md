# ProductHuntDB - Documentation

**Note**: This file contains documentation-specific instructions. See [root AGENTS.md](../AGENTS.md) for project-wide setup and conventions.

## Documentation Build Commands

### Quick Start

```bash
# From project root:

# Build HTML documentation
make docs
# or: cd docs && make html

# Live-reload development server (auto-rebuild on changes)
make htmllive
# or: cd docs && make livehtml

# Clean build artifacts
cd docs && make clean
```

### Live Development

The `livehtml` target provides the best authoring experience:

```bash
# Start live server (opens browser automatically)
make htmllive

# Server URL: http://127.0.0.1:8000
# Watches: docs/source/ and producthuntdb/ for changes
# Auto-rebuilds and reloads browser on save
```

Press `Ctrl+C` to stop the server.

## Documentation Structure

```
docs/
├── source/                 # Documentation source files
│   ├── index.md           # Homepage (MyST Markdown)
│   ├── changelog.md       # Project changelog
│   ├── conf.py            # Sphinx configuration
│   ├── _static/           # Custom CSS, JS, images
│   │   ├── css/custom.css
│   │   ├── js/
│   │   └── img/
│   ├── _templates/        # Custom HTML templates
│   │   └── partials/
│   └── tools/             # Per-tool documentation
│       ├── index.md
│       ├── alembic.md     # Alembic usage guide
│       ├── httpx.md       # HTTP client guide
│       ├── kaggle.md      # Kaggle integration
│       ├── pandas.md      # Data manipulation
│       ├── pydantic.md    # Data validation
│       ├── sqlmodel.md    # Database ORM
│       ├── typer.md       # CLI framework
│       └── uv.md          # Package manager
├── build/                 # Build output (git-ignored)
│   └── html/              # Generated HTML
└── Makefile              # Build automation
```

## Theme & Extensions

### Shibuya Theme

Modern, responsive Sphinx theme with:
- Dark/light mode toggle
- Sticky navigation
- Code copy buttons
- Search integration
- Mobile-friendly design

Config: `source/conf.py`, line ~70-100 (theme options)

### Key Extensions

Configured in `source/conf.py`:

**Content Authoring**:
- `myst_parser` - Markdown support (MyST flavor)
- `sphinx.ext.autodoc` - Auto-generate API docs from docstrings
- `autodoc_pydantic` - Enhanced Pydantic model documentation
- `sphinx_click` - Document Typer/Click CLI commands

**Enhanced Features**:
- `sphinx_copybutton` - Copy code blocks
- `sphinx_design` - Cards, grids, tabs, dropdowns
- `sphinx_tabs` - Tabbed content
- `sphinxcontrib_mermaid` - Mermaid diagrams
- `sphinx_togglebutton` - Collapsible sections

**Metadata & Navigation**:
- `sphinx_sitemap` - Generate sitemap.xml
- `autoclasstoc` - Auto-generate class TOCs
- `notfound.extension` - Custom 404 page

## Writing Documentation

### File Format

**Preferred**: MyST Markdown (`.md`)
- Full Markdown syntax
- Sphinx directives via `{directive}`
- Supports includes, cross-references, admonitions

**Also supported**: reStructuredText (`.rst`)

### MyST Markdown Syntax

```markdown
# Heading 1

Regular Markdown content.

## Code Blocks

\`\`\`python
# Python code with syntax highlighting
from producthuntdb import AsyncGraphQLClient
\`\`\`

## Admonitions

:::{note}
This is a note.
:::

:::{warning}
This is a warning.
:::

## Cross-References

Link to Python objects: {py:func}`producthuntdb.cli.main`

Link to other docs: [Tools](tools/index.md)

## Directives

\`\`\`{eval-rst}
.. autoclass:: producthuntdb.models.PostRow
   :members:
\`\`\`
```

### Documenting Python Code

**Docstring format**: Google style (preferred) or NumPy

```python
def fetch_posts(limit: int = 50) -> list[PostRow]:
    """Fetch posts from Product Hunt API.
    
    Args:
        limit: Maximum number of posts to retrieve (default: 50)
    
    Returns:
        List of PostRow objects
    
    Raises:
        APIError: If API request fails
    
    Example:
        >>> posts = fetch_posts(limit=10)
        >>> len(posts)
        10
    """
```

Autodoc will extract this into the documentation automatically.

### Adding New Documentation Pages

1. **Create file**: `docs/source/your_topic.md`
2. **Add to TOC**: Edit `docs/source/index.md` and add to `toctree`:

```markdown
\`\`\`{toctree}
:maxdepth: 2

your_topic
\`\`\`
```

3. **Build to verify**: `make htmllive` and check output

## Configuration Reference

### Key Settings (source/conf.py)

```python
project = "ProductHuntDB"
author = "Wyatt Walsh"

# Extensions list (line ~30-60)
extensions = [
    "sphinx.ext.autodoc",
    "myst_parser",
    # ... see conf.py for full list
]

# Theme config (line ~70-100)
html_theme = "shibuya"
html_theme_options = {
    # Dark mode, nav options, etc.
}

# MyST config (line ~110-130)
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    # ...
]
```

### Custom Styling

- **CSS**: `source/_static/css/custom.css` (automatically loaded)
- **JS**: `source/_static/js/` (add to `html_js_files` in conf.py)
- **Images**: `source/_static/img/`

## Documentation Dependencies

Installed via dependency group `docs` in `pyproject.toml`:

```bash
# Install docs dependencies
uv sync --group docs

# Verify Sphinx version
uv run sphinx-build --version
```

Key packages:
- `sphinx>=8.2.3` - Core documentation engine
- `shibuya>=2025.10.21` - Theme
- `myst-parser>=4.0.1` - Markdown parser
- `sphinx-autobuild>=2025.8.25` - Live reload server
- `autodoc-pydantic>=2.2.0` - Pydantic model docs

See full list: `pyproject.toml`, lines ~50-80

## Common Tasks

### Adding API Documentation

```markdown
# API Reference

\`\`\`{eval-rst}
.. automodule:: producthuntdb.models
   :members:
   :undoc-members:
   :show-inheritance:
\`\`\`
```

### Adding Mermaid Diagrams

```markdown
\`\`\`{mermaid}
graph LR
    A[Client] --> B[API]
    B --> C[Database]
\`\`\`
```

### Creating Tabbed Content

```markdown
::::{tab-set}

:::{tab-item} Python
\`\`\`python
# Python example
\`\`\`
:::

:::{tab-item} Bash
\`\`\`bash
# Bash example
\`\`\`
:::

::::
```

### Adding a Changelog Entry

Edit `docs/source/changelog.md`:

```markdown
## [0.2.0] - 2025-10-29

### Added
- New feature description

### Changed
- What was modified

### Fixed
- Bug fixes
```

## Build Output

- **HTML**: `docs/build/html/`
- **Entry point**: `docs/build/html/index.html`
- **Assets**: CSS, JS, images copied to `_static/`

```bash
# View built docs locally
open docs/build/html/index.html
```

## Documentation Validation

Validate documentation quality before committing:

```bash
# 1. Build without warnings
cd docs && make html
# Check output for warnings/errors

# 2. Check for broken links (requires sphinx-linkcheck)
cd docs && make linkcheck

# 3. Spell check (manual for now - consider adding vale/codespell)
grep -r "recieve\|teh\|thier" source/

# 4. Validate MyST syntax
uv run python -c "from myst_parser import create_md_parser; print('✓ MyST parser available')"
```

All checks should pass before pushing documentation changes.

## Troubleshooting

### Build Errors

**Missing dependencies**:
```bash
uv sync --group docs
```

**Import errors in autodoc**:
- Ensure `producthuntdb` is importable: `uv run python -c "import producthuntdb"`
- Check Python path in `conf.py` (should include project root)

**Mermaid diagrams not rendering**:
- Verify `sphinxcontrib.mermaid` in extensions
- Check browser console for JavaScript errors

### Live Server Issues

**Port 8000 already in use**:
```bash
# Kill existing server
pkill -f sphinx-autobuild
lsof -ti:8000 | xargs kill -9
```

**Changes not reloading**:
- Check terminal for build errors
- Try manual rebuild: `make docs`
- Restart live server

### Styling Issues

- Clear browser cache (Cmd+Shift+R on macOS)
- Check `custom.css` syntax
- Verify CSS file path in `conf.py` `html_static_path`

## CI/CD Integration

**Note**: No CI workflows configured yet. When adding CI for docs:

```yaml
# .github/workflows/docs.yml (example)
- name: Build documentation
  run: |
    uv sync --group docs
    cd docs && make html
    
- name: Deploy to GitHub Pages
  uses: peaceiris/actions-gh-pages@v3
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ./docs/build/html
```

## References

- [Root AGENTS.md](../AGENTS.md) - Project-wide conventions
- [Sphinx documentation](https://www.sphinx-doc.org/) (observed: 2025-10-29)
- [MyST Parser](https://myst-parser.readthedocs.io/) (observed: 2025-10-29)
- [Shibuya theme](https://shibuya.lepture.com/) (observed: 2025-10-29)
- [sphinx-autobuild](https://github.com/sphinx-doc/sphinx-autobuild) (observed: 2025-10-29)
