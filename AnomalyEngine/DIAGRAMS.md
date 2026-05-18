# System Diagram Documentation

This document describes the diagrams recommended for the Anomaly Engine project, what each diagram should show, and why each is useful.

## Recommended Diagrams

1. Component Diagram
2. Data Flow Diagram (DFD)
3. Sequence Diagram
4. Activity Diagram
5. ER Diagram
6. Deployment Diagram (optional)

---

## 1. Component Diagram

### Purpose

Shows the major application pieces and how they connect.

### What to include

- Streamlit frontend (`main.py`)
- FastAPI backend (`src/api/app.py`)
- SQLite database (`src/api/database.py`, `src/api/models.py`)
- Pipeline modules (`src/pipelines/`)
- Feature engineering / visualization modules (`src/components/`)
- Config and hyperparameter files (`configs/`, `artifacts/hyperparams/`)

### Why it matters

It gives a high-level architecture overview for developers and stakeholders.

---

## 2. Data Flow Diagram (DFD)

### Purpose

Shows how data moves through the system.

### What to include

- User login request from Streamlit to FastAPI (`/login`)
- Token issuance with role and return
- User profile requests (`/me`, `/me/notifications`)
- Analysis request from Streamlit to `/analyze`
- Role/permission validation
- Activity logging to `UserActivity`
- Cache lookup in SQLite
- Pipeline execution when cache misses
- Analysis logging to `UserAnalysis`
- Notification creation
- Response returned to Streamlit
- Admin user management flows (`/users` endpoints)
- Cache management (`/cache` endpoints)

### Why it matters

It clarifies how information travels and where decisions are taken.

---

## 3. Sequence Diagram

### Purpose

Shows runtime interaction and ordering between components.

### Recommended flows

- Login flow with role assignment
- User profile and notification retrieval
- Analyze flow with cache hit
- Analyze flow with cache miss (including activity logging)
- Admin user creation/management flows
- Cache management flows
- Logout flow

### Why it matters

It makes the exact request/response sequence easy to understand.

---

## 4. Activity Diagram

### Purpose

Shows the steps and decision points within a process.

### Recommended processes

- "Run Analysis" workflow
- Cache decision path: hit vs miss
- Realtime simulation flow

### Why it matters

It helps document conditional behavior and control flow.

---

## 5. ER Diagram

### Purpose

Models the database entities and relationships.

### What to include

- `User` table
  - `id` (PK)
  - `username` (unique)
  - `hashed_password`
  - `role` (user/analyst/admin)
  - `permissions` (JSON)
  - `is_active`
  - `created_at`
- `UserActivity` table
  - `id` (PK)
  - `user_id` (FK to User)
  - `action` (login, analyze, etc.)
  - `resource` (endpoint affected)
  - `details` (JSON metadata)
  - `created_at`
- `Notification` table
  - `id` (PK)
  - `user_id` (FK to User)
  - `title`
  - `message`
  - `type`
  - `is_read`
  - `read_at`
  - `created_at`
- `UserAnalysis` table
  - `id` (PK)
  - `user_id` (FK to User)
  - `config_hash`
  - `stock`, `mode`, `timeframe`
  - `start_date`, `end_date`
  - `features` (JSON)
  - `best_params` (JSON)
  - `metrics` (JSON)
  - `status` (success/error)
  - `duration_seconds`
  - `executed_at`
- `PipelineCache` table
  - `id` (PK)
  - `config_hash` (unique)
  - `stock`, `mode`, `timeframe`
  - `start_date`, `end_date`
  - `features` (JSON)
  - `best_params` (JSON)
  - `metrics` (JSON)
  - `data` (JSON)
  - `created_at`

### Why it matters

An ER diagram is about data, not object-oriented programming. It is appropriate because the project stores and retrieves structured data in a database.

### Why it is not tied to OOP

- ER diagrams describe entities, attributes, and relationships.
- They are used for database design and data modeling.
- You can use them for any system that persists data, regardless of whether the code uses classes or functional style.

### Class Diagram

```mermaid
classDiagram
  class AnalysisRequest {
    +stock: str
    +start_date: str
    +end_date: str
    +timeframe: str
    +features: list[str]
    +mode: str
    +from_mapping(config)
  }

  class PipelineResult {
    +data: DataFrame
    +labels: dict
    +metrics: dict
    +best_params: dict
    +model: Any
    +as_response(include_model)
  }

  class BaseAnalysisPipeline {
    <<abstract>>
    #_prepare_features()
    #_build_metrics(feature_df, label_sets)
    #_attach_labels(feature_df, label_sets)
    +run()*
  }

  class StaticAnalysisPipeline {
    +run()
  }

  class RealtimeAnalysisPipeline {
    +window_size: int
    +run()
  }

  class DataLoader {
    +load(stock, start_date, end_date)
  }
  class Preprocessor {
    +transform(df, timeframe)
  }

  class FeatureEngineering {
    +transform(df, features)
  }

  class FeatureScaler {
    +fit_transform(df, features)
  }

  class Evaluator {
    +compute(df, labels)
  }

  class AnomalyDetector {
    +predict(X, df, best_params)
  }

  BaseAnalysisPipeline <|-- StaticAnalysisPipeline
  BaseAnalysisPipeline <|-- RealtimeAnalysisPipeline
  BaseAnalysisPipeline --> AnalysisRequest
  BaseAnalysisPipeline --> DataLoader
  BaseAnalysisPipeline --> Preprocessor
  BaseAnalysisPipeline --> FeatureEngineering
  BaseAnalysisPipeline --> FeatureScaler
  BaseAnalysisPipeline --> AnomalyDetector
  StaticAnalysisPipeline --> PipelineResult
  RealtimeAnalysisPipeline --> PipelineResult
```

---

## 6. Deployment Diagram (optional)

### Purpose

Shows how the software is deployed and where each component runs.

### What to include

- User browser / client
- Streamlit host
- FastAPI host
- SQLite or other database host
- Optional reverse proxy / Docker

### Why it matters

It helps plan deployment and understand infrastructure requirements.

---

## How to use this documentation

- Use the Component Diagram for architecture reviews.
- Use the DFD for data movement and caching logic.
- Use Sequence Diagrams for request/response order.
- Use Activity Diagrams for workflows and decision points.
- Use ER Diagrams for database modeling.
- Use Deployment Diagrams if you need infrastructure documentation.

## Diagram tools

You can create these diagrams using any of the following:

- Mermaid
- Draw.io / diagrams.net
- Lucidchart
- PlantUML
- Microsoft Visio

---

## Mermaid Diagram Examples

### Component Diagram

```mermaid
flowchart TB
    Browser["Browser / Streamlit UI"] -->|Login / Analyze| FastAPI["FastAPI Backend"]
    FastAPI -->|Reads/Writes| DB["SQLite / SQLAlchemy DB"]
    FastAPI -->|Loads hyperparams| Hyperparams["artifacts/hyperparams"]
    FastAPI -->|Calls| AnalysisEngine["src/pipelines/analysis_engine.py"]
    FastAPI -->|Calls wrappers| StaticPipeline["src/pipelines/anomaly_detection_pipeline.py"]
    FastAPI -->|Calls wrappers| RealtimePipeline["src/pipelines/realtime_detection_pipeline.py"]
    FastAPI -->|Uses| Components["src/components/*"]
    Streamlit["Streamlit App\n(main.py)"] -->|API requests| FastAPI
```

### Data Flow Diagram (DFD)

```mermaid
flowchart TD
    User["User"] -->|Login request| Streamlit
    Streamlit -->|POST /login| FastAPI
    FastAPI -->|Validate credentials| DB
    FastAPI -->|Return token| Streamlit

    User -->|Run analysis| Streamlit
    Streamlit -->|POST /analyze| FastAPI
    FastAPI -->|Check cache| DB
    DB -->|Cache miss| FastAPI
    FastAPI -->|Run pipeline| Pipeline["Pipeline modules"]
    Pipeline -->|Result| FastAPI
    FastAPI -->|Save cache| DB
    FastAPI -->|Response| Streamlit
```

### Sequence Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant S as Streamlit
    participant A as FastAPI
    participant D as Database
    participant P as Pipeline

    U->>S: Click login
    S->>A: POST /login
    A->>D: Verify user
    D-->>A: User record
    A-->>S: Token

    U->>S: Click Run Analysis
    S->>A: POST /analyze
    A->>D: Lookup cache
    alt Cache hit
        D-->>A: Cached result
    else Cache miss
        D-->>A: No entry
        A->>P: Execute pipeline
        P-->>A: Analysis result
        A->>D: Save cache
    end
    A-->>S: Results
```

### Activity Diagram

```mermaid
flowchart TD
    Start([Start]) --> Login["Login required?"]
    Login -->|No| ShowLogin["Show login screen"]
    ShowLogin --> End
    Login -->|Yes| Choose["Select stock/timeframe/mode"]
    Choose --> Submit["Click Run Analysis"]
    Submit --> CheckCache["Cache lookup"]
    CheckCache -->|Hit| ReturnCached["Return cached results"]
    ReturnCached --> Visualize["Show visualizations"]
    CheckCache -->|Miss| RunPipeline["Run pipeline"]
    RunPipeline --> SaveCache["Save cache entry"]
    SaveCache --> Visualize
    Visualize --> End
```

### ER Diagram

```mermaid
erDiagram
    USER {
        int id PK
        string username
        string hashed_password
        bool is_active
        datetime created_at
    }
    PIPELINE_CACHE {
        int id PK
        string config_hash
        string stock
        string mode
        string timeframe
        string start_date
        string end_date
        json features
        json best_params
        json metrics
        json data
        datetime created_at
    }

    USER ||--o{ PIPELINE_CACHE : creates
```

> Note: the ER diagram uses a simple relationship for illustration. In this project the cache entries are not strictly owned by a single user yet, but the data model is still useful to document how database entities are structured.

---

## Notes

This project uses a relational data store for auth and caching, so ER diagrams are relevant even though the application code is not strictly object-oriented. The ER diagram documents the data model behind the FastAPI backend.
