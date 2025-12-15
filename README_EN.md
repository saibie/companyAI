# 🏢 Local Hierarchical AI Corp

> **A Local-First, Zero-Cost AI Organization Simulator.**
> Build and manage a hierarchical team of AI agents running entirely on your local machine using **Ollama**, **Django**, and **LangGraph**.

## 📖 Overview

**Local Hierarchical AI Corp** is a simulation platform where you act as the human CEO managing a recursive structure of AI agents. Unlike flat agent systems, this project emphasizes a **Command & Control** hierarchy:

* **CEO (You):** Define high-level goals and approve/reject results.
* **Managers:** Decompose tasks and delegate them to subordinates.
* **Subordinates:** Execute atomic tasks (Search, Code, Plan) or report back issues.

All AI inference happens locally via **Ollama**, ensuring privacy and zero API costs.

---

## ✨ Key Features

### 🧠 Intelligent Agent Workflow
* **Hierarchical Logic:** Agents can hire (`create_sub_agent`), fire (`fire_sub_agent`), and delegate tasks (`assign_task`) to their own subordinates.
* **Native Tool Calling:** Powered by **LangGraph** and Ollama's tool calling API (MCP-style scripts), replacing fragile regex parsing.
* **Recursive Delegation:** Tasks are broken down top-down and reported bottom-up.

### 🛠️ Tech Stack & Architecture
* **Backend:** Django 6.0 (Alpha features simulated), Python 3.12.
* **AI Engine:** **Ollama** (Llama 3.1, Mistral, Qwen, etc.).
* **Orchestration:** **LangGraph** (Stateful multi-turn agent loops).
* **Database:** PostgreSQL 16 + **pgvector** (for Vector Memory & RAG).
* **Frontend:** Django Templates + **HTMX** (Dynamic, SPA-like experience).
* **Infrastructure:** Docker Compose (All-in-one setup).

### 👁️ Human-in-the-Loop Dashboard
* **Recursive Organizational Tree:** Visualize the entire company hierarchy at a glance (CEO -> Managers -> Staff).
* **Task Approval System:** Review agent outputs. Approve them to proceed or Reject with feedback for revision.
* **Live Monitoring:** Watch agents "Think" and use tools in real-time via background workers.

---

## 🚀 Getting Started

### Prerequisites
1.  **Docker & Docker Compose** installed.
2.  **Ollama** installed and running on your host machine (or an accessible network location).
3.  (Optional) `uv` for local python package management.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/local-ai-corp.git](https://github.com/your-username/local-ai-corp.git)
    cd local-ai-corp
    ```

2.  **Configure Environment:**
    * Open `docker-compose.yml`.
    * Set `OLLAMA_HOST` to your machine's IP address (e.g., `http://host.docker.internal:11434` or your actual LAN IP).
    * *Note: `localhost` inside Docker refers to the container, not your machine.*

3.  **Run with Docker:**
    ```bash
    docker-compose up --build -d
    ```

4.  **Create Admin Account:**
    ```bash
    docker exec -it ai_corp_web python manage.py createsuperuser
    ```

5.  **Access the Dashboard:**
    * Go to: `http://localhost:8000/`

---

## 🕹️ Usage Guide

### 1. Hire Your First Manager
* On the Dashboard, go to **Create New Agent**.
* Enter Name (e.g., "Alice"), Role (e.g., "CTO"), and leave Manager as "No Manager" (Direct report to CEO).
* Click **Create Agent**.

### 2. Assign a Task
* Go to **Create New Task**.
* Select "Alice" as the assignee.
* Title: "Market Research", Description: "Research the latest trends in Agentic AI and draft a plan."
* Click **Create Task**.

### 3. Watch the Magic
* The background worker (`run_agents`) picks up the task.
* The agent will:
    * **Plan:** Create a step-by-step plan using `create_plan`.
    * **Search:** Use `search_web` tool.
    * **Delegate:** If the task is too big, it might hire a "Researcher" sub-agent and assign sub-tasks!
* Refresh the dashboard to see the Agent Tree grow dynamically.

### 4. Approve or Reject
* Once finished, the task appears in **Tasks Waiting Approval**.
* Review the **Result**.
    * ✅ **Approve:** The task is marked DONE.
    * ❌ **Reject:** Provide feedback. The agent will read your feedback and revise its plan.

---

## 📂 Project Structure

```text
.
├── corp/
│   ├── agent_workflow.py    # Core LangGraph logic & Native Tool Definitions
│   ├── models.py            # Agent, Task, AgentMemory (pgvector)
│   ├── views.py             # Dashboard & HTMX views
│   ├── management/
│   │   └── commands/
│   │       └── run_agents.py # Background worker for AI processing
│   └── templates/           # UI Templates (Recursive Agent Tree)
├── docker-compose.yml       # Service Orchestration
├── requirements.txt         # Python Dependencies
└── README.md                # This file
```

---

## 🛡️ License

This project is open-source and available under the MIT License.