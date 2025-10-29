# HTTPX - Modern HTTP Client

::::{grid} 2
:gutter: 3

:::{grid-item}
**Category:** Networking & API  
**Official Site:** [python-httpx.org](https://www.python-httpx.org/)  
**GitHub:** [encode/httpx](https://github.com/encode/httpx)  
**License:** BSD-3-Clause
:::

:::{grid-item}
**Version:** ≥0.28.1  
**Used For:** GraphQL API communication, HTTP/2 support, async requests  
**Why We Use It:** Modern async support, superior to requests library
:::

::::

---

## Overview

HTTPX is a fully featured HTTP client for Python 3, which provides sync and async APIs, and support for both HTTP/1.1 and HTTP/2.

### Key Features

- 🔄 **Async/Await Support** - Native async/await for concurrent requests
- 🚀 **HTTP/2** - Modern protocol support with multiplexing
- 🔌 **Connection Pooling** - Automatic connection reuse
- ⏱️ **Timeout Configuration** - Fine-grained timeout control
- 🍪 **Cookie Persistence** - Automatic cookie handling
- 🔐 **Authentication** - Built-in auth methods

---

## How ProductHuntDB Uses HTTPX

### 1. **GraphQL API Client**

ProductHuntDB uses HTTPX to communicate with Product Hunt's GraphQL API:

```python
import httpx
from typing import Dict, Any

class ProductHuntAPI:
    BASE_URL = "https://api.producthunt.com/v2/api/graphql"
    
    def __init__(self, api_token: str):
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(30.0, connect=10.0),
            http2=True,
        )
    
    async def query(self, query: str, variables: Dict[str, Any] = None) -> Dict:
        """Execute a GraphQL query."""
        response = await self.client.post(
            self.BASE_URL,
            json={"query": query, "variables": variables or {}},
        )
        response.raise_for_status()
        return response.json()
```

### 2. **Connection Pooling**

HTTPX automatically pools connections for efficiency:

```python
# Connection is reused across multiple requests
async with httpx.AsyncClient() as client:
    for page in range(1, 100):
        response = await client.post(url, json=get_query(page))
        process_response(response)
# Connections automatically closed when context exits
```

### 3. **Timeout Configuration**

Fine-grained timeout control for reliability:

```python
timeout = httpx.Timeout(
    timeout=30.0,      # Overall timeout
    connect=10.0,      # Connection timeout
    read=30.0,         # Read timeout
    write=10.0,        # Write timeout
)

client = httpx.AsyncClient(timeout=timeout)
```

### 4. **Error Handling**

Robust error handling with retries:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def fetch_with_retry(url: str) -> Dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
```

---

## Configuration in ProductHuntDB

### API Client Setup

```python
# producthuntdb/io.py
import httpx
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ph_api_token: str
    api_timeout: float = 30.0
    
settings = Settings()

# Create persistent client
api_client = httpx.AsyncClient(
    base_url="https://api.producthunt.com/v2/api/graphql",
    headers={
        "Authorization": f"Bearer {settings.ph_api_token}",
        "Content-Type": "application/json",
    },
    timeout=httpx.Timeout(settings.api_timeout),
    http2=True,
    limits=httpx.Limits(
        max_keepalive_connections=5,
        max_connections=10,
    ),
)
```

---

## Key Features Used

### Async Context Managers

```python
async with httpx.AsyncClient() as client:
    response = await client.get("https://api.example.com/data")
    data = response.json()
```

### Response Streaming

```python
async with httpx.AsyncClient() as client:
    async with client.stream("GET", url) as response:
        async for chunk in response.aiter_bytes():
            process_chunk(chunk)
```

### Custom Headers

```python
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "User-Agent": "ProductHuntDB/0.1.0",
}
client = httpx.AsyncClient(headers=headers)
```

### HTTP/2 Support

```python
# Enables multiplexing and server push
client = httpx.AsyncClient(http2=True)
```

---

## Performance Benefits

### Async vs Sync Comparison

| Operation | Sync (requests) | Async (httpx) | Improvement |
|-----------|-----------------|---------------|-------------|
| 100 sequential requests | 45s | 45s | - |
| 100 concurrent requests | 45s | 2.5s | **18x faster** |
| Connection overhead | High | Low | Pooling |

### Real-World Impact

- **API Syncing**: 1000 posts fetched in 30 seconds vs 15 minutes
- **Rate Limiting**: Better control with concurrent request limiting
- **Memory Usage**: Lower memory footprint with streaming

---

## Common Patterns

### GraphQL Query

```python
async def fetch_posts(cursor: str = None) -> Dict:
    query = """
    query($cursor: String) {
        posts(after: $cursor, first: 50) {
            edges {
                node {
                    id
                    name
                    tagline
                }
                cursor
            }
        }
    }
    """
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            API_URL,
            json={"query": query, "variables": {"cursor": cursor}},
            headers={"Authorization": f"Bearer {token}"},
        )
        return response.json()
```

### Pagination

```python
async def fetch_all_pages():
    cursor = None
    all_data = []
    
    async with httpx.AsyncClient() as client:
        while True:
            response = await fetch_page(client, cursor)
            data = response["data"]["posts"]
            all_data.extend(data["edges"])
            
            if not data["pageInfo"]["hasNextPage"]:
                break
            cursor = data["pageInfo"]["endCursor"]
    
    return all_data
```

### Rate Limiting

```python
import asyncio
from asyncio import Semaphore

async def rate_limited_fetch(urls: list[str], rate_limit: int = 10):
    semaphore = Semaphore(rate_limit)
    
    async def fetch_one(url: str):
        async with semaphore:
            async with httpx.AsyncClient() as client:
                return await client.get(url)
    
    tasks = [fetch_one(url) for url in urls]
    return await asyncio.gather(*tasks)
```

---

## Error Handling

### Status Code Checking

```python
response = await client.get(url)

# Raise exception for 4xx/5xx status codes
response.raise_for_status()

# Manual checking
if response.status_code == 200:
    data = response.json()
elif response.status_code == 429:
    # Rate limited
    await asyncio.sleep(60)
```

### Timeout Handling

```python
try:
    response = await client.get(url, timeout=10.0)
except httpx.TimeoutException:
    logger.error("Request timed out")
except httpx.HTTPStatusError as e:
    logger.error(f"HTTP error: {e.response.status_code}")
except httpx.RequestError as e:
    logger.error(f"Request error: {e}")
```

---

## Best Practices

::::{grid} 1 1 2 2
:gutter: 2

:::{grid-item-card} ✅ Do
- Use async clients for I/O-bound operations
- Enable HTTP/2 for better performance
- Configure timeouts for reliability
- Reuse clients with connection pooling
- Handle errors gracefully
:::

:::{grid-item-card} ❌ Don't
- Don't create a new client per request
- Don't ignore timeout configuration
- Don't mix sync and async in the same codebase
- Don't forget to close clients (or use context managers)
:::

::::

---

## Comparison with Requests

| Feature | requests | httpx |
|---------|----------|-------|
| Async Support | ❌ | ✅ |
| HTTP/2 | ❌ | ✅ |
| Streaming | Limited | Full |
| Type Hints | Partial | Complete |
| Performance | Good | Excellent |
| Learning Curve | Easy | Easy |

---

## Learn More

- 📚 [Official Documentation](https://www.python-httpx.org/)
- 🎓 [Async Tutorial](https://www.python-httpx.org/async/)
- 🔧 [Advanced Usage](https://www.python-httpx.org/advanced/)
- 🐛 [Issue Tracker](https://github.com/encode/httpx/issues)

---

## Related Tools

- [Tenacity](tenacity) - Retry logic for failed requests
- [Pydantic](pydantic) - Response validation
- [nest-asyncio](https://github.com/erdewit/nest_asyncio) - Nested event loop support

:::{seealso}
Check out the [Tenacity](tenacity) documentation for implementing robust retry logic with HTTPX.
:::
