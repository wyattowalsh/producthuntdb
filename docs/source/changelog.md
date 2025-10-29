# Changelog

All notable changes to the Frame Python project.

This changelog is **automatically generated** from git commit history and supports manual entries for special cases.

## Automated Git History

The following entries are automatically generated from git commits. For best results, use [Conventional Commits](https://www.conventionalcommits.org/) format:

- **`feat:`** - New features
- **`fix:`** - Bug fixes
- **`docs:`** - Documentation changes
- **`refactor:`** - Code refactoring
- **`test:`** - Test additions
- **`chore:`** - Maintenance tasks

```{eval-rst}
.. git_changelog::
   :revisions: 50
   :detailed-message-pre: True
   :filename_filter: python/.*
```

---

## Manual Entries & Release Notes

### Version 0.1.0 - Initial Release (2025-01-XX)

**Major Features:**

- ✨ **Documentation Site**: Beautiful Sphinx documentation with Shibuya theme, comprehensive API reference using autodoc2
- 🧠 **AI Package**: PydanticAI integration with AWS Bedrock for business validation
- 🌐 **REST API**: FastAPI-based REST service with OAuth2 authentication and interactive API documentation
- 💻 **CLI Application**: Typer-based command-line interface for business validation with beautiful terminal output
- 🔌 **MCP Server**: Model Context Protocol server for AI agent integration
- ⚙️ **Core Package**: Shared utilities including settings management (Pydantic Settings) and structured logging (Loguru)

**Architecture & Tooling:**

- 🐍 **Python 3.13**: Latest Python with cutting-edge features
- 📦 **UV Package Manager**: Fast, modern dependency management
- 🏗️ **Workspace Monorepo**: Clean separation of apps, packages, and tests
- 🎨 **Code Quality**: Ruff formatting, comprehensive linting, mypy type checking
- 📖 **Documentation**: Automated API docs, guides, and changelog

**Development Experience:**

- Migrated to Python 3.13 from earlier versions
- Adopted `uv` for lightning-fast dependency management
- Restructured as workspace monorepo for better organization
- Fixed type hints throughout codebase
- Ensured Pydantic v2 compatibility

**What's Next:**

- Expanded test coverage
- Additional AI validation capabilities
- Enhanced CLI features
- Performance optimizations

---

## How to Contribute to Changelog

### Conventional Commit Format

Use conventional commits for automatic changelog generation:

```bash
# Features
git commit -m "feat(api): add webhook support for payment notifications"

# Bug fixes  
git commit -m "fix(ai): resolve authentication timeout in AWS Bedrock"

# Documentation
git commit -m "docs(guides): update setup instructions"

# Breaking changes (add ! after type)
git commit -m "feat(core)!: redesign settings configuration API"
```

**Scopes:** `api`, `cli`, `mcp`, `ai`, `core`, `docs`

### Adding Manual Entries

For major releases, announcements, or migrations, add entries to the "Manual Entries & Release Notes" section above:

```markdown
### Version X.Y.Z - Release Name (YYYY-MM-DD)

**Description of the release...**

**Major Changes:**
- Feature description
- Breaking change with migration guide

**Migration Guide:**
1. Step one
2. Step two
```

### When to Add Manual Entries

- 📦 **Major version releases** - Comprehensive overview and migration guides
- ⚠️ **Breaking changes** - Detailed migration instructions
- 🔒 **Security updates** - CVE references and remediation steps
- 📢 **Deprecation notices** - Timeline and alternatives
- 🎯 **Feature milestones** - Significant feature completions

---

## Commit Message Guidelines

### Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Examples

**Good:**
```bash
feat(api): add rate limiting for authentication endpoints

Implements configurable rate limits per IP address to prevent
brute force attacks. Defaults to 5 requests per minute.

Closes #234
```

**With Breaking Change:**
```bash
feat(core)!: redesign settings configuration API

BREAKING CHANGE: Settings must now be loaded via Settings.load()
instead of direct instantiation. See migration guide in docs.
```

**Bug Fix:**
```bash
fix(ai): resolve timeout issue in AWS Bedrock connection

Fixed connection timeout by implementing exponential backoff
retry strategy with max 3 attempts.

Fixes #456
```

### Commit Types

| Type | Purpose | Example |
|------|---------|---------|
| `feat` | New feature | `feat(api): add webhook notifications` |
| `fix` | Bug fix | `fix(cli): correct JSON output formatting` |
| `docs` | Documentation | `docs(setup): update installation guide` |
| `style` | Code style | `style(core): apply black formatting` |
| `refactor` | Refactoring | `refactor(api): extract validation logic` |
| `perf` | Performance | `perf(ai): optimize query execution` |
| `test` | Tests | `test(api): add webhook integration tests` |
| `chore` | Maintenance | `chore(deps): update dependencies` |
| `ci` | CI/CD | `ci(github): add automated testing` |

---

## Versioning

This project adheres to [Semantic Versioning](https://semver.org/):

- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality (backward compatible)
- **PATCH** version for backward compatible bug fixes

### Release Process

1. Update version in `pyproject.toml`
2. Add manual entry to changelog if needed
3. Create git tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
4. Push tag: `git push origin vX.Y.Z`
5. Documentation auto-updates on build

---

## Resources

- **[Conventional Commits](https://www.conventionalcommits.org/)** - Commit message specification
- **[Semantic Versioning](https://semver.org/)** - Version numbering  
- **[Keep a Changelog](https://keepachangelog.com/)** - Changelog best practices
- **[sphinx-git Documentation](http://sphinx-git.readthedocs.io/)** - Git history integration
