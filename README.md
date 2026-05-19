# AI Workflow Platform

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![React](https://img.shields.io/badge/React-19.2-blue.svg)
![Framer Motion](https://img.shields.io/badge/Framer_Motion-10+-purple.svg)
![Prometheus](https://img.shields.io/badge/Prometheus-Monitoring-orange.svg)

An enterprise-grade, event-driven platform for executing, validating, and evaluating AI tasks asynchronously. The platform leverages a robust Python backend with a decoupled background worker architecture, paired with a stunning, high-performance React dashboard.

---

## 🏗 System Architecture

The application is built on a modern decoupled architecture to handle long-running AI evaluations and asynchronous task processing reliably.

```mermaid
graph TD
    %% Define Nodes
    User([User / Browser])
    Dashboard[React Dashboard\n(Framer Motion, Axios)]
    API[FastAPI Gateway\n(Port 8000)]
    Worker[Background Task Worker\n(Multiprocess)]
    DB[(SQL Database\nTasks, Workflows, DLQ)]
    Prometheus([Prometheus\nMetrics Scraper])
    AIService((Mock / Real\nOpenAI Service))

    %% Define Relationships
    User -->|Views/Interacts| Dashboard
    Dashboard -->|REST API /tasks| API
    API <-->|Reads/Writes Tasks| DB
    Worker <-->|Polls for QUEUED tasks| DB
    Worker <-->|Executes & Evaluates| AIService
    Worker -->|Writes DLQ on failure| DB
    Prometheus -->|Scrapes /metrics| API
    Worker -.->|Multiprocess Metrics| API

    %% Styling
    classDef frontend fill:#0f172a,stroke:#3b82f6,stroke-width:2px,color:#fff;
    classDef backend fill:#1e293b,stroke:#10b981,stroke-width:2px,color:#fff;
    classDef db fill:#334155,stroke:#f59e0b,stroke-width:2px,color:#fff;
    classDef external fill:#475569,stroke:#ec4899,stroke-width:2px,color:#fff;
    
    class Dashboard frontend;
    class API,Worker backend;
    class DB db;
    class Prometheus,AIService external;
```

---

## ✨ Key Features

### 🖥️ Project-Grade Frontend Dashboard
- **Glassmorphism Theme:** Dark-mode UI with immersive ambient gradients and blur effects.
- **Physics-Based Animations:** Powered by `framer-motion` for fluid row entrances, layout shifts, and modal interactions.
- **Real-time Pagination:** Clean API-driven pagination for handling vast amounts of historical tasks without browser lag.
- **Deep JSON Introspection:** Intelligently parses backend `result` schemas to render Score Gauges, Severity Pills, and recommendation cards.
- **Live Auto-Refresh:** Polling layer with non-intrusive `react-hot-toast` notifications.

### ⚙️ Resilient Backend Processing
- **Asynchronous Workers:** Dedicated worker processes poll the database to handle long-running tasks without blocking the main API gateway.
- **Dead Letter Queue (DLQ):** Tasks that exhaust their maximum retry counts are safely persisted to a DLQ for later auditing and recovery.
- **Pydantic Validation:** Strict API response boundaries ensure data integrity and accurate OpenAPI documentation.
- **Global Error Handling:** Consistent 500-level error formatting across all endpoints.

### 📈 Built-in Observability
- **Prometheus Metrics:** Native multiprocess metrics collection tracking throughput, latency histograms, error rates, and AI confidence scores.

---

## 🛠️ Technology Stack

| Domain | Technology | Purpose |
|---|---|---|
| **Frontend** | React 19, Framer Motion, Vanilla CSS | UI Rendering & Animations |
| **Backend API** | FastAPI, Pydantic, Uvicorn | REST Gateway & Schema Validation |
| **Database** | SQLAlchemy | ORM for Task & Workflow states |
| **Observability** | Prometheus Client | Scraping and metric aggregation |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Prometheus (Optional, for metrics)

### 1. Start the Backend API
Navigate to the root directory and start the FastAPI server:
```bash
# Install dependencies
pip install -r requirements.txt

# Run the API server
uvicorn apps.api.main:app --reload
```
*The API will be available at `http://localhost:8000`*

### 2. Start the Background Worker
In a new terminal window, start the task worker to begin processing the queue:
```bash
python apps/api/worker_main.py
```

### 3. Start the Frontend Dashboard
Navigate to the frontend directory and start the React app:
```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm start
```
*The dashboard will be available at `http://localhost:3000`*

### 4. Prometheus Metrics (Optional)
Start your local Prometheus instance using the provided configuration:
```bash
prometheus.exe --config.file=prometheus.yml
```
*Metrics are exposed at `http://localhost:8000/metrics`*

---

## 📖 API Reference

### `GET /tasks`
Fetch paginated tasks.
- **Query Params:** `skip` (int, default: 0), `limit` (int, default: 20)
- **Response:** `PaginatedTaskResponse` (contains `items`, `total`, `skip`, `limit`)

### `GET /tasks/{task_id}`
Fetch a specific task by ID.

### `PUT /tasks/{task_id}/status`
Update a task's status and result, triggering workflow completion checks.

---

## 🧪 Mock Mode (Development)
By default, the `analyze_logs` and `generate_recommendation` tasks bypass direct OpenAI calls to prevent `429 Insufficient Quota` errors during local development. The worker returns deterministic JSON payloads mimicking the AI service.

To restore real AI evaluation, uncomment the imports inside `apps/api/services/task_worker.py`.
