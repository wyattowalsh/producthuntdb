# Typer - CLI Framework

::::{grid} 2
:gutter: 3

:::{grid-item}
**Category:** CLI  
**Official Site:** [typer.tiangolo.com](https://typer.tiangolo.com/)  
**GitHub:** [tiangolo/typer](https://github.com/tiangolo/typer)  
**License:** MIT
:::

:::{grid-item}
**Version:** Latest  
**Used For:** Building the `producthuntdb` CLI with typed commands and automatic help  
**Why We Use It:** Simple, fast, and integrates with type hints for intuitive CLIs
:::

::::

---

## Overview

Typer builds on Click and uses Python type hints to generate beautiful CLIs with minimal boilerplate.

## How ProductHuntDB Uses Typer

- Core CLI (`producthuntdb`) is implemented with Typer for commands like `sync`, `export`, `publish`, and migration helpers.
- Automatic help, argument parsing, and completion support.

### Example

```python
import typer

app = typer.Typer()

@app.command()
def sync(max_pages: int = 10, verbose: bool = False):
    """Sync data from Product Hunt"""
    # implementation

if __name__ == '__main__':
    app()
```

## Best Practices

- Keep commands focused and composable.
- Use type hints for automatic validation and clear help text.
- Add tests for CLI entry points with `CliRunner`.

## Learn More

- 📚 [Typer Documentation](https://typer.tiangolo.com/)
- 🐛 [Issue Tracker](https://github.com/tiangolo/typer/issues)

:::{seealso}
See [Click](https://click.palletsprojects.com/) for the underlying implementation details.
:::

