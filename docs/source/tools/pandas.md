# Pandas - Data Processing

::::{grid} 2
:gutter: 3

:::{grid-item}
**Category:** Data & Processing  
**Official Site:** [pandas.pydata.org](https://pandas.pydata.org/)  
**GitHub:** [pandas-dev/pandas](https://github.com/pandas-dev/pandas)  
**License:** BSD-3-Clause
:::

:::{grid-item}
**Version:** Latest  
**Used For:** CSV/Parquet export, in-memory data transformations, aggregation  
**Why We Use It:** Ubiquitous, powerful, and well-optimized for tabular data
:::

::::

---

## Overview

Pandas is the de-facto library for tabular data manipulation in Python. It provides the DataFrame abstraction with fast IO, groupby/aggregation, joins, and time-series helpers.

## How ProductHuntDB Uses Pandas

- Export database tables to CSV for downstream publishing (Kaggle exports).
- Lightweight transformations and sample exports used in QA and data previews.
- Converting query results into DataFrame for reports and plots.

### Common Patterns

```python
import pandas as pd

# Read a CSV
df = pd.read_csv('data/export/posts.csv')

# Simple aggregation
top = df.groupby('name')['votes_count'].sum().sort_values(ascending=False).head(10)

# Export
df.to_csv('data/export/posts-clean.csv', index=False)
```

## Best Practices

- Prefer chunked IO for very large tables (`pd.read_csv(..., chunksize=100000)`).
- Use explicit dtypes when possible to reduce memory usage.
- Keep heavy ETL off the main sync path (do batch exports/transformations asynchronously).

## Learn More

- 📚 [Pandas Documentation](https://pandas.pydata.org/docs/)
- 🐛 [Issue Tracker](https://github.com/pandas-dev/pandas/issues)

:::{seealso}
See [Kaggle API](kaggle) for publishing exported CSVs.
:::

