# 🚀 AI Workflow Automation Platform

A production-ready AI-powered workflow system that processes incidents, analyzes logs, generates recommendations, and provides observability through metrics and dashboards.

---

## 🔥 Live Demo

* 🌐 Frontend: https://your-vercel-url.vercel.app
* ⚙️ Backend API: https://ai-workflow-platform.onrender.com
* 📊 API Docs: https://ai-workflow-platform.onrender.com/docs

---

## 🧠 What This Project Does

This system simulates a real-world **AI incident response pipeline**:

1. Incident is created
2. Workflow is triggered
3. Tasks are queued
4. Background worker processes tasks
5. AI analyzes logs
6. System generates recommendations
7. Results + metrics are stored and visualized

---

## 🏗️ Architecture

```
Frontend (React - Vercel)
        ↓
FastAPI Backend (Render)
        ↓
PostgreSQL (Render)
        ↓
Background Worker (Thread inside FastAPI)
        ↓
AI + Evaluation + Metrics
```

---

## ⚙️ Tech Stack

### Backend

* FastAPI
* SQLAlchemy
* PostgreSQL
* Background worker (thread-based queue system)
* Prometheus metrics

### Frontend

* React (Create React App)
* Axios

### DevOps / Deployment

* Render (API + DB)
* Vercel (Frontend)
* GitHub (CI/CD)

---

## 📊 Key Features

* ✅ Asynchronous task processing
* 🔁 Retry + backoff mechanism
* 🚫 Dead Letter Queue (DLQ) handling
* 🧠 AI log analysis + evaluation scoring
* 📈 Metrics (latency, retries, failures, DLQ)
* 📡 Observability-ready (Prometheus compatible)
* 🌐 Full-stack deployment

---

## 🧪 API Endpoints (Core)

| Method | Endpoint                            | Description        |
| ------ | ----------------------------------- | ------------------ |
| POST   | `/incidents`                        | Create incident    |
| POST   | `/workflows/{id}/run/{incident_id}` | Trigger workflow   |
| GET    | `/tasks`                            | Fetch recent tasks |
| GET    | `/tasks/{id}`                       | Task details       |

---

## 🖥️ Frontend Features

* Task dashboard
* Status tracking (Completed / Failed / Queued)
* AI evaluation score display
* Real-time refresh
* Detailed task inspection

---

## 🚀 Local Setup

### 1. Clone repo

```bash
git clone https://github.com/your-username/ai-workflow-platform.git
cd ai-workflow-platform
```

---

### 2. Backend setup

```bash
pip install -r requirements.txt
uvicorn apps.api.main:app --reload
```

---

### 3. Frontend setup

```bash
cd frontend
npm install
npm start
```

---

## 🌍 Deployment

### Backend (Render)

* Web Service (FastAPI + Worker thread)
* PostgreSQL (Free tier)

### Frontend (Vercel)

* Connected to backend via environment variable

```env
REACT_APP_API_URL=https://ai-workflow-platform.onrender.com
```

---

## 📈 Observability

* Task success/failure tracking
* Retry metrics
* DLQ monitoring
* Latency histograms

---

## 💡 Design Decisions

* Worker merged into FastAPI to support **free deployment**
* Retry logic with exponential backoff
* Strict task state transitions using enums
* Fault-tolerant pipeline (DLQ for failures)

---

## 🚧 Future Improvements

* WebSocket real-time updates
* Authentication + multi-user support
* Advanced AI evaluation (LLM scoring)
* Grafana dashboard integration
* Distributed worker system (Celery / Kafka)

---

## 💣 Challenges Solved

* Handling async workflows without Celery
* Building retry + DLQ system from scratch
* Observability with Prometheus metrics
* Deploying worker system on free tier

---

## 📌 Author

Built by Nandu Panakanti

---

## Please ⭐ If you like this project :)

Give it a star ⭐ — it helps!
