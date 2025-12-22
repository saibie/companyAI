# 🏢 Local Hierarchical AI Corp

> **A Local-First, Zero-Cost AI Organization Simulator.**
> Build and manage a hierarchical team of AI agents running entirely on your local machine using **Ollama**, **Django**, and **LangGraph**.

## 📖 Overview

**Local Hierarchical AI Corp** is a simulation platform where you act as the human CEO managing a recursive structure of AI agents.

Unlike flat agent systems, this project emphasizes a **Command & Control** hierarchy and **Multi-tenancy**:

* **CEO (You):** Each logged-in user operates their own isolated "Virtual Corp". You define high-level goals and approve/reject results.
* **Managers:** Decompose tasks and delegate them to subordinates.
* **Subordinates:** Execute atomic tasks (Search, Code, Plan) or report back issues.
* **Corporate Wiki:** Successfully completed tasks are automatically archived into the **Company Wiki**, becoming organizational assets.

All AI inference happens locally via **Ollama**, ensuring privacy and zero API costs.

---

## ✨ Key Features

### 🧠 Intelligent Agent Workflow
* **Hierarchical Logic:** Agents can hire (`create_sub_agent`), fire (`fire_sub_agent`), and delegate tasks (`assign_task`) to their own subordinates.
* **Native Tool Calling:** Powered by **LangGraph** and Ollama's tool calling API for higher accuracy.
* **Recursive Delegation:** Tasks are broken down top-down and reported bottom-up.

### 📚 Corporate Knowledge Management (Wiki)
* **Auto-Archiving:** When an agent completes a task (Done), the result is automatically embedded and saved to the **Wiki**.
* **Knowledge Retrieval:** Before starting a task, agents search the Wiki for past success stories or SOPs (Standard Operating Procedures).

### 🔐 User Ownership & Security
* **Multi-tenancy:** All agents, tasks, and wiki data are strictly isolated per **logged-in user (Owner)**.
* **UUID Implementation:** All data models use UUIDv4 for enhanced security and scalability.

### 👁️ Human-in-the-Loop Dashboard
* **Recursive Organizational Tree:** Visualize the entire company hierarchy (CEO -> Managers -> Staff) at a glance.
* **Task Approval System:** Review agent outputs. Approve to complete or Reject with feedback for revision.

---

## 🛠️ Tech Stack

* **Backend:** Django 5.x (Future-proof for 6.0), Python 3.12
* **AI Engine:** **Ollama** (Llama 3.1, Mistral, Qwen, etc.)
* **Orchestration:** **LangGraph** (Stateful Multi-agent Workflow)
* **Database:** PostgreSQL 16 + **pgvector** (Vector Store & RAG)
* **Frontend:** Django Templates + **HTMX** (Dynamic SPA Experience)
* **Infrastructure:** Docker Compose

---

## 🚀 Getting Started

### Prerequisites
1.  **Docker & Docker Compose** installed.
2.  **Ollama** installed and running on your host machine.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/local-ai-corp.git](https://github.com/your-username/local-ai-corp.git)
    cd local-ai-corp
    ```

2.  **Configure Environment:**
    * Open `docker-compose.yml`.
    * Set `OLLAMA_HOST` to your machine's IP address (e.g., `http://host.docker.internal:11434` or your actual LAN IP).

3.  **Run with Docker:**
    ```bash
    docker-compose up --build -d
    ```

4.  **Create Admin Account (Required):**
    * Login is mandatory for multi-tenancy support.
    ```bash
    docker exec -it ai_corp_web python manage.py createsuperuser
    ```

5.  **Access & Login:**
    * Go to: `http://localhost:8000/`
    * **Login** with the account you created to access the dashboard.

---

## 🕹️ Usage Guide

1.  **Hire Your First Manager:** On the Dashboard, click [Create New Agent] to hire a direct report (Manager set to "No Manager").
2.  **Assign a Task:** Use [Create New Task] to give instructions (e.g., "Research competitor AI trends").
3.  **Watch & Approve:** Watch agents think and hire subordinates in the background. Approve finished work in [Tasks Waiting Approval].
4.  **Check the Wiki:** Verify that approved results are saved in the [Company Wiki] tab.

---

## 🛡️ License

This project is open-source and available under the MIT License.