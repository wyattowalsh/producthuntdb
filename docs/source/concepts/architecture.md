# Pipeline Architecture

ProductHuntDB embraces a layered architecture that keeps domain concerns isolated and testable.

```{mermaid}
graph TB
    subgraph "📦 Storage"
        db[(SQLite<br/>producthunt.db)]
        csv[[CSV Exports]]
    end

    subgraph "🔄 Pipeline"
        sync["DataPipeline<br/>(producthuntdb.pipeline)"]
        export["Export Manager<br/>(producthuntdb.repository)"]
        kaggle["Kaggle Manager<br/>(producthuntdb.kaggle)"]
    end

    subgraph "🛠️ Core Services"
        models["SQLModel schema<br/>(producthuntdb.models)"]
        settings["Typed settings<br/>(producthuntdb.config.Settings)"]
        client["GraphQL client<br/>(producthuntdb.api.AsyncGraphQLClient)"]
        logger["Loguru logger<br/>(producthuntdb.logging)"]
    end

    subgraph "🌐 External"
        phapi["Product Hunt GraphQL v2"]
        kaggleApi["Kaggle REST API"]
    end

    cli["Typer CLI<br/>(producthuntdb.cli)"]

    cli --> sync
    cli --> export
    cli --> kaggle

    sync --> client
    sync --> models
    sync --> settings
    sync --> logger
    sync --> db

    export --> repository["Repository layer"]
    repository --> db
    export --> csv

    kaggle --> export
    kaggle --> kaggleApi

    client --> phapi
```

## Layer Responsibilities

- **Interface layer** (`producthuntdb.cli`): Typer commands orchestrate flows and provide rich feedback via Rich tables and Loguru logging.
- **Pipeline layer** (`producthuntdb.pipeline.DataPipeline`): Coordinates GraphQL fetches, deduplication, and persistence. Concurrency and retry policies live here.
- **Core services**: Composed of the API client, SQLModel data structures, and Pydantic settings. Each component can be swapped for testing via dependency injection.
- **Storage**: SQLite for canonical data, CSV exports for downstream distribution, and Kaggle for external publishing.

## Dependency Injection

`DataPipeline` accepts injected implementations for the GraphQL client and database manager, simplifying unit and integration testing. Refer to :mod:`producthuntdb.interfaces` for the Protocol definitions used to structure these dependencies.

## Observability

- Logging is centralized through `producthuntdb.logging.logger`.
- The configuration layer exposes toggles for JSON logs and OpenTelemetry endpoints.
- CLI commands include verbose switches to surface HTTP payloads when diagnosing issues.
