# Tenacity - Retry Logic

::::{grid} 2
:gutter: 3

:::{grid-item}
**Category:** Retry & Resilience  
**Official Site:** [tenacity.readthedocs.io](https://tenacity.readthedocs.io/)  
**GitHub:** [jd/tenacity](https://github.com/jd/tenacity)  
**License:** MIT
:::

:::{grid-item}
**Version:** Latest  
**Used For:** Robust retry strategies for network/API calls  
**Why We Use It:** Flexible policies, backoff strategies, and easy integration
:::

::::

---

## Overview

Tenacity is a lightweight library for adding retries with configurable stop/wait strategies and failure handling.

## How ProductHuntDB Uses Tenacity

- Retry HTTP requests to Product Hunt API and transient DB operations.
- Use exponential backoff with jitter for rate-limited endpoints.

### Example

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=30))
def fetch_data():
    # network call
    pass
```

## Best Practices

- Keep retries idempotent or ensure operations are safe to repeat.
- Use backoff+jitter to avoid thundering herds.
- Limit total retry time for long-running operations.

## Learn More

- 📚 [Tenacity Docs](https://tenacity.readthedocs.io/)
- 🐛 [Issue Tracker](https://github.com/jd/tenacity/issues)

:::{seealso}
See [HTTPX](httpx) for combining retries with network calls.
:::

