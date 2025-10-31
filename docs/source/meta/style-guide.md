# Documentation Style Guide

Consistent docs are easier to navigate, translate, and maintain. Adopt the following conventions when adding or updating content.

## Tone & Voice

- Write in the second person (“you”) and focus on user tasks.
- Prefer short, direct sentences. Highlight the “why” before the “how”.
- Use inclusive examples and neutral language.

## Structure

- Every page opens with an H1 that matches the sidebar title.
- Provide context in the first paragraph, then list prerequisites.
- Break procedures into numbered steps and include copy-pasteable commands.
- Use callouts (`{note}`, `{warning}`) for critical information.

## Terminology

- **CLI** refers to `uv run producthuntdb` commands. Always show the `uv run` prefix.
- **Pipeline** refers to the orchestration in `producthuntdb.pipeline`.
- Use American English spelling (synchronize, initialize).

## Formatting

- Keep line length ≤ 100 characters in code blocks to avoid wrapping in Shibuya’s layout.
- Use fenced code blocks with language hints (` ```bash `, ` ```python `).
- Prefer tables for option matrices and feature comparisons.
- For cross-references, use explicit links (`{doc}`) or `:mod:` for Python modules.

## Sphinx Design Components

- Prefer `{card}` blocks inside `{grid}` containers when displaying multiple choices.
- Keep `grid` layouts under four columns for readability on mobile.
- Use `dropdown` or `tabs` for advanced/optional content instead of long bullet lists.
- Avoid nesting more than two interactive components (for example, tabs inside accordions).

## Metadata & Search

- Update `docsearch_options` in `conf.py` when Algolia credentials change.
- Add new environment variables to the [Automation & CI Runbook](../guides/automation).
- Keep `extlinks` up to date so badges and issue links resolve correctly.

## Autodoc Hygiene

- Ensure public classes and functions include docstrings—they render automatically in the API reference.
- Update `__all__` exports when adding new public entry points.
- Document new enums or settings in `producthuntdb.config` so `autodata` sections stay accurate.

## Accessibility

- Provide descriptive link text (“Open architecture diagram”) instead of “here”.
- Ensure images supply alt text; prefer vector assets for logos.
- Avoid emoji-only labels in headings. Pair emoji with text (“🚀 Start”).

## Review Checklist

- Run `make docs` and address warnings (nitpicky mode is enabled).
- Run `sphinx-build -b linkcheck docs/source docs/build/linkcheck`.
- Verify new headings appear in the correct toctree.
- Update this style guide and navigation links when introducing new patterns.
