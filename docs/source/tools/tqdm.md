# tqdm - Progress Bars

::::{grid} 2
:gutter: 3

:::{grid-item}
**Category:** UX / CLI  
**Official Site:** [tqdm.github.io](https://tqdm.github.io/)  
**GitHub:** [tqdm/tqdm](https://github.com/tqdm/tqdm)  
**License:** MPL-2.0
:::

:::{grid-item}
**Version:** Latest  
**Used For:** Progress bars in CLI and batch jobs  
**Why We Use It:** Lightweight, familiar, and thread-safe progress UI
:::

::::

---

## Overview

tqdm is a small library that provides fast, extensible progress bars for loops and iterators.

## How ProductHuntDB Uses tqdm

- Showing progress when exporting large tables to CSV.
- Used in batch processing jobs and long-running import operations.

### Example

```python
from tqdm import tqdm

for row in tqdm(rows):
    process(row)
```

## Best Practices

- Use `tqdm(total=...)` for known-length tasks.
- Disable progress bars in CI or when output is non-interactive.

## Learn More

- 📚 [tqdm Docs](https://tqdm.github.io/)
- 🐛 [Issue Tracker](https://github.com/tqdm/tqdm/issues)

:::{seealso}
See [Typer](typer) for examples of integrating progress bars into CLI commands.
:::

