# System Diagram Documentation

This document describes the diagrams recommended for the Anomaly Engine project, what each diagram should show, and why each is useful.

## Recommended Diagrams

1. Component Diagram
2. Data Flow Diagram (DFD)
3. Sequence Diagram
4. Activity Diagram
5. ER Diagram
6. Deployment Diagram (optional)




### Report-ready ER Diagram

This ER diagram is suitable to include in a technical report. It lists primary keys (PK), foreign keys (FK), and attributes relevant for compliance and data retention reviews.

```mermaid


erDiagram

  USER {
    int id PK
    string username UK
    string hashed_password
    string role
    datetime created_at
  }

  USER_ACTIVITY {
    int id PK
    int user_id FK
    string action
    string resource
    json details
    datetime created_at
  }

  USER_ANALYSIS {
    int id PK
    int user_id FK
    string config_hash
    string stock
    string timeframe
    date start_date
    date end_date
    json best_params
    json metrics
    string data_path
    bool is_favorite
    string status
    int duration_seconds
    datetime executed_at
  }


  EXPLANATION {
    int id PK
    int analysis_id FK
    int user_id FK
    string artifact_path
    string artifact_hash
    string model
    string model_version
    string summary
    json highlights
    json entries
    int anomaly_count
    json meta
    datetime created_at
  }

  USER ||--o{ USER_ACTIVITY : logs
  USER ||--o{ USER_ANALYSIS : performs
  USER ||--o{ EXPLANATION : creates
  USER_ANALYSIS ||--o{ EXPLANATION : has


```

## System Flowchart (Mermaid) 2026-06-07

This flowchart shows the high-level runtime interactions between the UI, API, pipeline engine, storage and auxiliary services.

```mermaid

---
config:
  theme: default
---
flowchart LR
 subgraph UI["UI"]
        Browser["Browser / AnomalyUI (React)"]
  end
    Browser -- Login / Analyze / List --> FastAPI["FastAPI Backend (src/api/app.py)"]
    FastAPI -- Authenticate / Token --> Security["security.py"]
    FastAPI -- DB read/write --> DB["SQLite / SQLAlchemy"]
    FastAPI -- Run pipeline --> AnalysisEngine["AnalysisEngine"]
    AnalysisEngine --> DataLoader["DataLoader"] & Preprocessor["Preprocessor"] & FeatureEng["FeatureEngineering"] & Scaler["FeatureScaler"] & Detector["AnomalyDetectorService"]
    Detector --> DBSCAN["DBSCAN"] & IsolationForest["IsolationForest"]
    AnalysisEngine -- Detection Output --> FeatureStore["Anomaly Rows + Model Outputs"]
    FastAPI -- Generate explanation request --> ExplanationEngine["ExplanationEngine"]
    ExplanationEngine -- Consumes --> FeatureStore
    ExplanationEngine -- "LLM-powered reasoning" --> LLM["Azure/OpenAI ChatCompletions API"]
    ExplanationEngine -- Optional context retrieval --> NewsAPI["Tavily News Search API"]
    ExplanationEngine -- Fallback if AI fails --> Heuristic["Rule-based Heuristic"]
    FastAPI -- Log User Activity --> Notifications["UserActivity"]
    FastAPI -- Return results --> Browser
```

Note: Z-Score is included as an optional side analysis feature in the flowchart. The main anomaly detection path is through `DBSCAN` and `IsolationForest`, with AI explanation context enriched by the News API.

Refer to the other diagrams in this document for more detailed component, sequence and ER diagrams.


## 7. Class Diagrams

### 7.1 Analyst Class Diagram

```mermaid
classDiagram
    class User {
        +id: int
        +username: str
        +email: str
        +role: str = "admin"
        +email_verified : bool
        +created_at : datetime
        +hashed_password: str
    }

    class AnalysisEngine {
        +config: AnalysisRequest
        +best_params: dict
        +run()
        +_prepare_features()
        +_build_metrics()
        +_attach_labels()
    }

    class ExplanationEngine {
        +request: AnomalyExplanationRequest
        +explain()
        +build_prompt(payload, search_context)
        +_extract_anomaly_rows(data)
        +_build_search_context(stock, rows)
    }

    class UserAnalysis {
        +id: int
        +user_id: int
        +stock: str
        +timeframe: str
        +best_params: json
        +metrics: json
        +data_path: str
        +is_favorite: bool
        +executed_at: datetime
    }

    class Explanation {
        +id: int
        +analysis_id: int
        +user_id: int
        +artifact_path: str
        +artifact_hash: str
        +summary: str
        +entries: json
        +anomaly_count: int
        +created_at: datetime
    }

    User --> AnalysisEngine : executes analysis
    User --> ExplanationEngine : requests explanation
    User --> UserAnalysis : reads/ creates
    AnalysisEngine --> UserAnalysis : generates results
    ExplanationEngine --> Explanation : produces explanation
```

### 7.2 Admin Class Diagram

```mermaid
classDiagram
    class User {
        +id: int
        +username: str
        +email: str
        +role: str = "admin"
        +email_verified : bool
        +created_at : datetime
        +hashed_password: str
    }

    class AnalysisEngine {
        +config: AnalysisRequest
        +best_params: dict
        +run()
        +_prepare_features()
        +_build_metrics()
        +_attach_labels()
    }

    class ExplanationEngine {
        +request: AnomalyExplanationRequest
        +explain()
        +build_prompt(payload, search_context)
        +_extract_anomaly_rows(data)
        +_build_search_context(stock, rows)
    }

    class UserAnalysis {
        +id: int
        +user_id: int
        +stock: str
        +timeframe: str
        +best_params: json
        +metrics: json
        +data_path: str
        +is_favorite: bool
        +executed_at: datetime
    }

    class Explanation {
        +id: int
        +analysis_id: int
        +user_id: int
        +artifact_path: str
        +artifact_hash: str
        +summary: str
        +entries: json
        +anomaly_count: int
        +created_at: datetime
    }


    class UserActivity {
        +id: int
        +user_id: int
        +action: str
        +resource: str
        +details: json
        +created_at: datetime
    }

 

    User --> AnalysisEngine : executes analysis
    User --> ExplanationEngine : requests explanation
    User --> UserAnalysis : reads / creates
    User --> UserActivity : reads activity logs
    AnalysisEngine --> UserAnalysis : generates results
    ExplanationEngine --> Explanation : produces explanation
```

## 8. Component Diagram

```mermaid
flowchart TB
    Browser[Browser / UI]
    Backend[Backend / FastAPI]
    AnalysisEngine[AnalysisEngine]
    ExplanationEngine[ExplanationEngine]
    DB[SQLite Database]
    Artifacts[Artifact Storage]
    Scraper[Scraper Service]

    Browser -->|login / analyze / explain| Backend
    Backend -->|runs analysis| AnalysisEngine
    Backend -->|requests explanation| ExplanationEngine
    Backend -->|reads/writes| DB
    Backend -->|stores artifacts| Artifacts
    Backend -->|starts scrape job| Scraper
    Scraper -->|updates data files| Artifacts
```

## 9. Deployment Diagram

```mermaid
flowchart TB
    Browser[Browser / React UI]
    WebApp[AnomalyUI Web Client]
    API[FastAPI Backend Server]
    LocalDisk[Local Storage / artifacts/]
    Database[SQLite Database File]
    AIService[External AI Service]
    ScraperService[Scraper Task]

    Browser --> WebApp
    WebApp --> API
    API --> Database
    API --> LocalDisk
    API --> AIService
    API --> ScraperService
    ScraperService --> LocalDisk
```

## 10. Object Diagram

```mermaid
objectDiagram
    object analyst : Analyst {
        id: 1
        username: "analyst_user"
        role: "analyst"
    }
    object analysisEngine : AnalysisEngine {
        config: {stock: "SBI", timeframe: "1D"}
    }
    object explanationEngine : ExplanationEngine {
        request: {stock: "SBI", timeframe: "1D"}
    }
    object userAnalysis : UserAnalysis {
        id: 101
        stock: "SBI"
        is_favorite: false
    }
    object explanation : Explanation {
        id: 201
        anomaly_count: 3
    }

    analyst --> analysisEngine
    analyst --> explanationEngine
    analysisEngine --> userAnalysis
    explanationEngine --> explanation
```

## 11. State Diagram

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> AnalysisRequested : submit analysis
    AnalysisRequested --> AnalysisRunning : run pipeline
    AnalysisRunning --> AnalysisCompleted : success
    AnalysisRunning --> AnalysisFailed : failure
    AnalysisCompleted --> Favorited : mark favorite
    AnalysisCompleted --> ExplanationRequested : request explanation
    ExplanationRequested --> ExplanationGenerating : generate explanation
    ExplanationGenerating --> ExplanationStored : save artifact
    ExplanationStored --> Viewed : view
    Viewed --> [*]
```

## 12. Sequence Diagram

```mermaid
sequenceDiagram
    participant Analyst
    participant Backend
    participant AnalysisEngine
    participant DB
    participant ExplanationEngine
    participant Storage

    Analyst->>Backend: POST /analyze
    Backend->>AnalysisEngine: execute(config)
    AnalysisEngine->>DB: read stock data
    AnalysisEngine-->>Backend: results
    Backend->>Storage: save artifact
    Backend->>DB: create UserAnalysis
    Backend-->>Analyst: return analysis response

    Analyst->>Backend: POST /analyze/explain
    Backend->>ExplanationEngine: explain(request)
    ExplanationEngine->>Storage: optional search/context
    ExplanationEngine-->>Backend: explanation
    Backend->>DB: create Explanation
    Backend-->>Analyst: return explanation response
```

## 13. Activity Diagram

```mermaid
flowchart TD
    Start([Start])
    Login[Analyst logs in]
    Submit[Submit analysis request]
    RunPipeline[Run AnalysisPipeline]
    StoreResult[Store UserAnalysis]
    ReturnResult[Return results to user]
    RequestExplain[Request explanation]
    GenerateExplain[Generate explanation]
    StoreExplain[Store Explanation artifact]
    ReturnExplain[Return explanation to user]
    End([End])

    Start --> Login --> Submit --> RunPipeline --> StoreResult --> ReturnResult --> RequestExplain --> GenerateExplain --> StoreExplain --> ReturnExplain --> End
```

