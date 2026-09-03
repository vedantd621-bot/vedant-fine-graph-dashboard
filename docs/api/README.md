# FinGraph REST API Architecture & Services

The **FinGraph REST API** exposes real-time graph intelligence, topological fraud alerts, GDS centrality & community metrics, explainable risk assessments, forensic money trails, and simulated administrative freeze actions.

---

## 1. Architecture Overview

```text
       Simulator (Python)
              │
              ▼
         Apache Kafka
              │
              ▼
         Apache Flink
              │
              ▼
         Neo4j 5.18
         ├── Constraints & Indexes
         ├── GDS 2.6 (PageRank, WCC, Louvain)
         └── Cypher Fraud Detectors
              │
              ▼
         FastAPI Backend (Port 8000)
         ├── Alert Service & Status Lifecycle
         ├── Account Dossiers & Risk Engine
         ├── Bounded Subgraph Visualizer
         └── Forensic Money Trail Tracer
              │
              ▼
         React 18 + TypeScript Dashboard (Port 5173 / 3000)
```

---

## 2. API Design Principles

1. **Uniform JSON Envelopes**:
   - Single resource: `{"data": { ... }, "meta": { ... }}`
   - Collections: `{"data": [ ... ], "pagination": { "page": 1, "page_size": 20, "total_items": 100, ... }}`
   - Error diagnostics: `{"error": {"code": "RESOURCE_NOT_FOUND", "message": "..."}}`
2. **Safe Traversal Boundaries**:
   - Subgraph neighborhood queries enforce bounded `depth` ($1..3$), `max_nodes` ($\le 200$), and `max_edges` ($\le 500$).
   - Money trail tracing bounds maximum hops ($1..6$).
3. **Auditability & Explainability**:
   - All risk scores expose granular contributing reasons and subscores ($60\%$ rule $+ 40\%$ graph).
4. **Interactive OpenAPI Documentation**:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

---

## 3. Local Startup

```bash
# Start FastAPI backend
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Or using compatibility launcher
uvicorn api.src.main:app --host 0.0.0.0 --port 8000 --reload
```
