# ProductHuntDB - Documentation

**Parent**: See [root AGENTS.md](../AGENTS.md) for project-wide setup and conventions.

**Scope**: Documentation-specific build, preview, and publishing instructions.

## Overview

Sphinx-based documentation with MyST Markdown, Shibuya theme, and live-reload development server. Build with `make docs`, develop with `make htmllive`.

## Documentation Build Commands

### Quick Start

```bash
# From project root:

# Build HTML documentation
make docs

# Live-reload dev server (auto-opens browser at http://127.0.0.1:8000)
make htmllive

# Clean build artifacts
cd docs && make clean
```

### Live Development

The `htmllive` target provides the best authoring experience:

```bash
# Start live server (opens browser automatically)
make htmllive

# Server URL: http://127.0.0.1:8000
# Watches: docs/source/ and producthuntdb/ for changes
# Auto-rebuilds and reloads browser on save
```

Press `Ctrl+C` to stop the server.

## Documentation Structure

```text
docs/
├── source/                 # Documentation source files
│   ├── index.md           # Homepage (MyST Markdown)
│   ├── changelog.md       # Project changelog
│   ├── conf.py            # Sphinx configuration
│   ├── _static/           # Custom CSS, JS, images
│   ├── _templates/        # Custom HTML templates
│   └── tools/             # Per-tool documentation
├── build/html/            # Build output (gitignored)
└── Makefile              # Build automation
```

Full structure: View `docs/source/` directory

## Theme & Extensions

### Shibuya Theme

Modern, responsive Sphinx theme with dark/light mode, sticky navigation, code copy buttons, search integration, and mobile-friendly design.

Config: `source/conf.py` (lines ~70-100 for theme options)

### Key Extensions

**Content Authoring**: `myst_parser` (Markdown), `sphinx.ext.autodoc` (API docs), `autodoc_pydantic` (Pydantic models), `sphinx_click` (CLI docs)

**Enhanced Features**: `sphinx_copybutton`, `sphinx_design` (cards/grids/tabs), `sphinxcontrib_mermaid` (diagrams), `sphinx_togglebutton`

**Metadata**: `sphinx_sitemap`, `autoclasstoc`

Full list: `source/conf.py` extensions section

## Writing Documentation

### File Format

**Preferred**: MyST Markdown (`.md`) - Full Markdown syntax, Sphinx directives via `{directive}`, supports includes, cross-references, admonitions

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
```

Full MyST syntax: [MyST Parser docs](https://myst-parser.readthedocs.io/) (observed: 2025-10-30)

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
2. **Add to TOC**: Edit `docs/source/index.md` and add to `toctree`
3. **Build to verify**: `make htmllive` and check output

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

## Build Output

- **HTML**: `docs/build/html/`
- **Entry point**: `docs/build/html/index.html`
- **Assets**: CSS, JS, images copied to `_static/`

```bash
# View built docs locally
open docs/build/html/index.html
```

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
- [Sphinx documentation](https://www.sphinx-doc.org/) (observed: 2025-10-30)
- [MyST Parser](https://myst-parser.readthedocs.io/) (observed: 2025-10-30)
- [Shibuya theme](https://shibuya.lepture.com/) (observed: 2025-10-30)
- [sphinx-autobuild](https://github.com/sphinx-doc/sphinx-autobuild) (observed: 2025-10-30)
