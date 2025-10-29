# docs/source/conf.py
# SPDX-License-Identifier: MIT
"""
Sphinx configuration for ProductHuntDB documentation.

ProductHuntDB is a comprehensive Python toolkit for collecting, storing, and analyzing
Product Hunt data via the GraphQL API v2.

Key choices:
- Theme: shibuya (rich navbar/socials, edit-this-page, clean ToC)
- Markdown: MyST with a broad set of extensions
- API docs: autodoc + napoleon for comprehensive coverage
- Inter-project links: intersphinx (Python/Pydantic/SQLModel/httpx)
- Sitemap ready for SEO
"""

from __future__ import annotations

from datetime import date
import os
from pathlib import Path
import sys

# --------------------------------------------------------------------------------------
# Paths & repo metadata
# --------------------------------------------------------------------------------------

DOCS_DIR        = Path(__file__).resolve().parent
REPO_ROOT       = DOCS_DIR.parent.parent  # docs/source -> docs -> repo root
PKG_ROOT        = REPO_ROOT / "producthuntdb"
PROJECT_SLUG    = "producthuntdb"
ORG_SLUG        = "wyattowalsh"
DEFAULT_BRANCH  = os.getenv("DOCS_BRANCH", "main")

# Make producthuntdb package importable
sys.path.insert(0, str(REPO_ROOT))

# --------------------------------------------------------------------------------------
# Project information
# --------------------------------------------------------------------------------------

project   = "ProductHuntDB"
author    = "Wyatt Walsh"
copyright = f"{date.today().year}, {author}"
version   = os.getenv("PRODUCTHUNTDB_VERSION", "0.1.0")
release   = version

# --------------------------------------------------------------------------------------
# General configuration
# --------------------------------------------------------------------------------------

extensions = [
    # Core / structure
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.extlinks",

    # Markdown
    "myst_parser",

    # Authoring UX / components
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_tabs.tabs",
    "sphinx_togglebutton",
    "sphinxemoji.sphinxemoji",

    # Diagrams
    "sphinxcontrib.mermaid",

    # API & typing quality
    "sphinx_autodoc_typehints",
    "autoclasstoc",
    "sphinxcontrib.autodoc_pydantic",  # Pydantic model documentation

    # Repo-aware / meta
    "sphinx_git",  # Automated changelog from git history

    # SEO
    "sphinx_sitemap",
]

templates_path   = ["_templates"]
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "**/.ipynb_checkpoints",
    "**/site-packages/**",
    "**/__pycache__/**",
    "**/.venv/**",
    "**/.uv/**",
]
source_suffix = {
    ".rst": "restructuredtext",
    ".md" : "markdown",
}
language = "en"
default_role = "py:obj"  # short refs resolve to Python objects
nitpicky = False          # Set to True for stricter checking

# --------------------------------------------------------------------------------------
# Theme: shibuya
# --------------------------------------------------------------------------------------

html_theme       = "shibuya"
html_title       = f"{project} Documentation"
html_short_title = "ProductHuntDB"
html_static_path = ["_static"]

# Favicon configuration - using ProductHuntDB logo SVG with auto light/dark theming
html_favicon = "_static/img/favicon/favicon.svg"

# Additional favicons and web app manifest - these will be copied to _static/
html_extra_path = [
    "_static/img/favicon/site.webmanifest",
]

# Show "last updated" timestamp
html_last_updated_fmt = "%b %d, %Y"

# Add source links to pages
html_show_sourcelink = True

# Display module names in signatures
add_module_names = True

# Use index as root
html_use_index = True

# Generate comprehensive index
html_domain_indices = True

html_css_files   = [
    "css/custom.css",
    "css/components.css",
    "css/lucide-icons.css",
]
html_js_files    = [
    "js/custom.js",
]

# App icons / repo links / announcement / TOC control
html_theme_options = {
    # Logos for dark/light - ProductHuntDB custom logo with auto light/dark theming
    "light_logo": "_static/img/logo.svg",
    "dark_logo" : "_static/img/logo.svg",

    # Social & repo
    "github_url"   : f"https://github.com/{ORG_SLUG}/{PROJECT_SLUG}",

    # Color theme - using orange/red to match Product Hunt branding
    "accent_color": "orange",
    
    # Dark code blocks for better contrast
    "dark_code": True,

    # Sidebar & global ToC behavior
    "toctree_collapse": False,      # Keep sections expanded
    "toctree_maxdepth": 3,          # Show up to 3 levels deep
    "toctree_titles_only": False,   # Show full hierarchy
    "toctree_includehidden": True,  # Include hidden toctree entries

    # Navbar links - using proper emoji unicode for icons
    "nav_links": [
        {"title": "🚀 Getting Started", "url": "index#quick-start"},
        {"title": "📊 Data Coverage", "url": "index#data-coverage"},
        {"title": "🔧 CLI Reference", "url": "index#cli-reference"},
        {"title": "🛠️ Tools", "url": "tools/index"},
        {"title": "📝 Changelog", "url": "changelog"},
    ],

    # Social links
    "twitter_url": None,
    "discord_url": None,
}

# Edit-this-page context
html_context = {
    "source_type"      : "github",
    "source_user"      : ORG_SLUG,
    "source_repo"      : PROJECT_SLUG,
    "source_version"   : DEFAULT_BRANCH,
    "source_docs_path" : "/docs/source/",
}

# --------------------------------------------------------------------------------------
# MyST (Markdown) configuration
# --------------------------------------------------------------------------------------

myst_enable_extensions = {
    "attrs_block",
    "attrs_inline",
    "colon_fence",
    "deflist",
    "dollarmath",
    "amsmath",
    "fieldlist",
    "linkify",
    "substitution",
    "tasklist",
    "html_image",
    "replacements",
    "smartquotes",
}
myst_heading_anchors = 3  # auto-anchors for h1..h3
myst_links_external_new_tab = True

# --------------------------------------------------------------------------------------
# Autodoc / autosummary / napoleon / typehints
# --------------------------------------------------------------------------------------

# Standard autodoc settings
autodoc_default_options = {
    "members"          : True,
    "member-order"     : "bysource",
    "special-members"  : "__init__",
    "undoc-members"    : True,
    "exclude-members"  : "__weakref__",
    "show-inheritance" : True,
    "inherited-members": False,
}
autodoc_typehints              = "description"
autodoc_typehints_description_target = "documented"
autodoc_type_aliases           = {}
autodoc_class_signature        = "separated"
autodoc_member_order           = "bysource"
autodoc_preserve_defaults      = True
autodoc_warningiserror         = False

# Autosummary: auto-generate stub pages for modules/classes
autosummary_generate           = True
autosummary_generate_overwrite = False
autosummary_imported_members   = True
autosummary_ignore_module_all  = False

# Napoleon: support for NumPy & Google style docstrings
napoleon_numpy_docstring       = True
napoleon_google_docstring      = True
napoleon_use_param             = True
napoleon_use_rtype             = True
napoleon_use_ivar              = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes    = True
napoleon_use_admonition_for_references = True
napoleon_preprocess_types      = True
napoleon_attr_annotations      = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True

# sphinx-autodoc-typehints: rich type hint rendering
typehints_fully_qualified         = False
typehints_use_signature           = True
typehints_use_signature_return    = True
typehints_document_rtype          = True
typehints_defaults                = "comma"
typehints_use_rtype               = True
always_document_param_types       = True
set_type_checking_flag            = True
typehints_formatter               = None

# --------------------------------------------------------------------------------------
# autodoc2 — import-free API docs (DISABLED - using standard autodoc instead)
# --------------------------------------------------------------------------------------

# ProductHuntDB uses standard autodoc + napoleon for API documentation
# autodoc2 is disabled as we have a simpler single-package structure

# Warnings - suppress common warnings
suppress_warnings = [
    "ref.python",  # Suppress missing reference warnings for external modules
    "myst.header",  # Suppress MyST header warnings
    "toc.not_included",  # Suppress warnings for intentionally excluded docs
]

# Ignore specific type hint references for runtime-only dependencies
nitpick_ignore_regex = [
    # Runtime-only dependencies
    (r"py:.*", r"tenacity.*"),
    (r"py:.*", r"boto3.*"),
    (r"py:.*", r"botocore.*"),
    (r"py:.*", r"pydantic_ai.*"),
    (r"py:.*", r"loguru.*"),
    (r"py:.*", r"typer.*"),
    # AWS types
    (r"py:.*", r"mypy_boto3.*"),
    # Internal/typing constructs
    (r"py:.*", r"typing_extensions.*"),
    (r"py:.*", r"_.*"),  # Private modules
]

# --------------------------------------------------------------------------------------
# autoclasstoc — enhance class documentation
# --------------------------------------------------------------------------------------

autoclasstoc_sections = [
    "public-attrs",
    "public-methods",
    "private-attrs",
    "private-methods",
]

# --------------------------------------------------------------------------------------
# autodoc_pydantic — special handling for Pydantic models
# --------------------------------------------------------------------------------------

autodoc_pydantic_model_show_json            = True
autodoc_pydantic_model_show_config_summary  = True
autodoc_pydantic_model_show_field_summary   = True
autodoc_pydantic_model_member_order         = "bysource"
autodoc_pydantic_model_undoc_members        = True
autodoc_pydantic_settings_show_json         = False
autodoc_pydantic_settings_show_config_summary = True
autodoc_pydantic_settings_show_field_summary = True
autodoc_pydantic_settings_member_order      = "bysource"
autodoc_pydantic_field_show_constraints     = True
autodoc_pydantic_field_show_default         = True

# --------------------------------------------------------------------------------------
# Intersphinx — cross-link into external docs
# --------------------------------------------------------------------------------------

intersphinx_mapping = {
    "python"    : ("https://docs.python.org/3", None),
    "pydantic"  : ("https://docs.pydantic.dev/latest", None),
    # "httpx"     : ("https://www.python-httpx.org", None),  # No objects.inv available
    # "sqlmodel"  : ("https://sqlmodel.tiangolo.com", None),  # No objects.inv available
    "alembic"   : ("https://alembic.sqlalchemy.org/en/latest", None),
    "sqlalchemy": ("https://docs.sqlalchemy.org/en/20", None),
    "click"     : ("https://click.palletsprojects.com/en/stable", None),
    # "kaggle"    : ("https://www.kaggle.com/docs/api", None),  # No objects.inv available
}
intersphinx_disabled_domains = []
intersphinx_timeout          = 30

# --------------------------------------------------------------------------------------
# Copybutton (UX for code blocks)
# --------------------------------------------------------------------------------------

copybutton_prompt_text        = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp   = True
copybutton_remove_prompts     = True
copybutton_only_copy_prompt_lines = False
copybutton_line_continuation_character = "\\"

# --------------------------------------------------------------------------------------
# Tabs / togglebutton / emoji
# --------------------------------------------------------------------------------------

sphinxemoji_style = "twemoji"

# --------------------------------------------------------------------------------------
# Mermaid diagrams
# --------------------------------------------------------------------------------------

# Use client-side rendering via JavaScript (raw HTML mode)
# This doesn't require Chromium/Puppeteer and renders in the browser
mermaid_version = "10.9.1"
mermaid_output_format = "raw"  # Use "raw" for client-side rendering (no Chromium needed)
mermaid_init_js = """
mermaid.initialize({
    startOnLoad: true,
    theme: 'base',
    themeVariables: {
        primaryColor: '#325054',
        primaryTextColor: '#fff',
        primaryBorderColor: '#456366',
        lineColor: '#587578',
        secondaryColor: '#4C8788',
        tertiaryColor: '#f8f6f2',
        background: '#ffffff',
        mainBkg: '#325054',
        secondBkg: '#587578',
        mainContrastColor: '#fff',
        darkMode: false,
        fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif',
        fontSize: '16px'
    },
    flowchart: {
        curve: 'basis',
        padding: 20,
        nodeSpacing: 50,
        rankSpacing: 50,
        diagramPadding: 20,
        htmlLabels: true,
        useMaxWidth: true
    },
    securityLevel: 'loose'
});
"""

# --------------------------------------------------------------------------------------
# Viewcode / Source Links
# --------------------------------------------------------------------------------------

viewcode_follow_imported_members = True
viewcode_enable_epub             = False

# --------------------------------------------------------------------------------------
# Sphinx Git Integration
# --------------------------------------------------------------------------------------

sphinx_git_show_branches = True

# --------------------------------------------------------------------------------------
# API Documentation Display Enhancements
# --------------------------------------------------------------------------------------

add_module_names = True
autodoc_typehints = "description"
python_use_unqualified_type_names = True
python_display_short_literal_types = True
maximum_signature_line_length = 88

# --------------------------------------------------------------------------------------
# Not Found (404) - OPTIONAL
# Uncomment if sphinx-notfound-page is installed
# --------------------------------------------------------------------------------------

# notfound_context = {
#     "title"     : "Page Not Found",
#     "body"      : "Sorry, we couldn't find that page.",
# }
# notfound_urls_prefix = "/"

# --------------------------------------------------------------------------------------
# HTML base URL
# --------------------------------------------------------------------------------------

html_baseurl         = "http://localhost:8000/"
sitemap_url_scheme   = "{link}"

# --------------------------------------------------------------------------------------
# Linkcheck
# --------------------------------------------------------------------------------------

linkcheck_ignore = [
    r"^http://localhost",
    r"^https://localhost",
]

# --------------------------------------------------------------------------------------
# Todo extension
# --------------------------------------------------------------------------------------

todo_include_todos = True

# --------------------------------------------------------------------------------------
# External links
# --------------------------------------------------------------------------------------

extlinks = {
    "issue": (f"https://github.com/{ORG_SLUG}/{PROJECT_SLUG}/issues/%s", "issue %s"),
    "pr": (f"https://github.com/{ORG_SLUG}/{PROJECT_SLUG}/pull/%s", "PR %s"),
}

# --------------------------------------------------------------------------------------
# HTML base URL for sitemap
# --------------------------------------------------------------------------------------

html_baseurl = os.getenv("DOCS_BASE_URL", "https://wyattowalsh.github.io/producthuntdb/")

