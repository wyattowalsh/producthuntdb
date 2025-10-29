# Loguru - Logging

::::{grid} 2
:gutter: 3

:::{grid-item}
**Category:** Logging  
**Official Site:** [loguru.readthedocs.io](https://loguru.readthedocs.io/)  
**GitHub:** [Delgan/loguru](https://github.com/Delgan/loguru)  
**License:** MIT
:::

:::{grid-item}
**Version:** Latest  
**Used For:** Application logging with structured and human-friendly output  
**Why We Use It:** Simple configuration, sink management, and pretty logs
:::

::::

---

## Overview

Loguru provides a developer-friendly logging API that simplifies configuration and sinks while keeping good defaults.

## How ProductHuntDB Uses Loguru

- Centralized logger across CLI and background tasks.
- Structured messages for easier parsing in CI logs.

### Example

```python
from loguru import logger

logger.add('logs/producthuntdb.log', rotation='10 MB', retention='10 days')
logger.info('Starting sync for %s posts', count)
```

## Best Practices

- Use sinks for file + console separation.
- Avoid printing secrets; filter sensitive fields before logging.
- Use structured context (bindings) for request/post IDs.

## Learn More

- 📚 [Loguru Docs](https://loguru.readthedocs.io/)
- 🐛 [Issue Tracker](https://github.com/Delgan/loguru/issues)

:::{seealso}
See [Typer](typer) for CLI-driven logging configuration examples.
:::

