# 📂 PROJECT SPECIFICATION: Local Hierarchical AI Corp

**Version:** 1.0 (Final Draft)
**Target Framework:** Django (v5.x with v6.0 readiness), Docker, Ollama, LangGraph
**Objective:** Build a local-first, zero-cost AI organization simulator where a human CEO manages hierarchical AI agents.

---

## 1. Core Philosophy
* **Local First:** All inference must happen locally using **Ollama**. No external paid APIs (OpenAI, Anthropic, etc.).
* **Hierarchical Logic:** Agents have a recursive structure (Parent-Child). Tasks are decomposed Top-down and reported Bottom-up.
* **Resource Efficiency:** Use a single Database container (PostgreSQL + pgvector) instead of multiple vector DBs.
* **Human-in-the-Loop:** Critical decisions (Approve/Reject) require CEO interaction.

---

## 2. Technology Stack & Environment

| Component | Technology | Detail |
| :--- | :--- | :--- |
| **Containerization** | **Docker Compose** | Orchestrate App + DB. |
| **Backend** | **Django 5.x+** | Core logic, Admin UI, ORM. (Design with Django 6.0 async/background tasks in mind). |
| **Database** | **PostgreSQL 16+** | Relational data (Agents, Tasks). |
| **Vector Search** | **pgvector** | Extension for storing agent memories & embeddings. |
| **AI Engine** | **Ollama** | Local LLM server (Llama 3, Mistral, etc.). |
| **Orchestration** | **LangGraph** | State management for agent loops and approval flows. |
| **Frontend** | **Django Templates + HTMX** | SPA-like experience without React/Vue overhead. |

---

## 3. Database Schema Design (ERD)

**NOTE to Developer:** Use `pgvector.django` for the embedding field.

### A. `Agent` (Self-Referencing)
* `id`: PK
* `name`: CharField
* `role`: CharField (e.g., "CTO", "Junior Python Dev")
* `manager`: ForeignKey (`self`, null=True) - *Defines the hierarchy.*
* `config`: JSONField - Stores `ollama_model`, `temperature`, `system_prompt`.
* `is_active`: Boolean - *Soft delete logic for firing agents.*

### B. `Task` (Workflow State)
* `id`: PK
* `title`: CharField
* `description`: TextField
* `status`: Enum (`TODO`, `THINKING`, `WAIT_APPROVAL`, `APPROVED`, `DONE`, `REJECTED`)
* `creator`: ForeignKey (`Agent`)
* `assignee`: ForeignKey (`Agent`)
* `parent_task`: ForeignKey (`self`) - *For task decomposition.*
* `result`: TextField - *Final output of the task.*
* `feedback`: TextField - *Rejection reason from CEO/Parent.*

### C. `AgentMemory` (Vector Store)
* `id`: PK
* `agent`: ForeignKey (`Agent`)
* `content`: TextField - *The raw text memory.*
* `embedding`: **VectorField(768)** - *Compatible with `nomic-embed-text`.*
* `type`: CharField (`observation`, `reflection`, `sop`)
* `created_at`: DateTime

---

## 4. Implementation Logic & Flow

### Phase 1: Infrastructure Setup (Docker)
1.  Create `docker-compose.yml` with two services:
    * `db`: Image `pgvector/pgvector:pg16`.
    * `web`: Django container.
2.  Configure Django `settings.py` to use `pgvector` extension.

### Phase 2: The "Brain" Integration (Ollama + LangGraph)
1.  **Thinking Process:**
    * Create a generic `AgentNode` class in Python.
    * Input: Task Description + Past Memories (RAG).
    * Process: Call Ollama API (via LangChain).
    * Output: Structured Plan or Code.
2.  **Memory Retrieval:**
    * Before acting, the agent must query `AgentMemory` using Cosine Similarity (`<=>` operator in Postgres) to find relevant past mistakes or rules.

### Phase 3: The "Bureaucracy" (Approval Workflow)
1.  **Drafting:** Agent creates a report -> Status `WAIT_APPROVAL`.
2.  **Review (Human-in-the-Loop):**
    * CEO sees the task in Django Admin or Dashboard.
    * **Action A (Approve):** Status changes to `APPROVED` -> Agent executes next step.
    * **Action B (Reject):** CEO adds `feedback` -> Status changes to `TODO` -> Agent re-thinks considering the feedback.

---

## 5. Development Roadmap (Step-by-Step Instructions)

**Step 1: Scaffolding**
* Initialize Django project `core`.
* Define Models (`Agent`, `Task`, `AgentMemory`) in `models.py`.
* Generate Migrations (Ensure `VectorExtension()` is added).

**Step 2: Backend Logic**
* Implement `OllamaClient` class to handle LLM requests.
* Implement `MemoryManager` class to handle `INSERT` and `SELECT` (search) on `AgentMemory`.

**Step 3: Frontend (MVP)**
* Create a Dashboard view showing the Organization Tree (Recursive template).
* Create a "Task Inbox" for the CEO.

**Step 4: Background Worker**
* Since we are simulating Django 6.0 features, implement a simple Management Command (`python manage.py run_agents`) that loops through `Task`s in `IN_PROGRESS` state and processes them using Ollama.

---

## 6. Constraints & Guidelines for Developer Agent

1.  **DO NOT** write code that depends on OpenAI (`openai` pip package is forbidden unless used for Ollama compatibility).
2.  **DO** use `django-htmx` for dynamic interactions (no full page reloads).
3.  **DO** ensure the database migration explicitly enables the vector extension:
    ```python
    from pgvector.django import VectorExtension
    operations = [VectorExtension(), ...]
    ```
4.  **Keep it Modular:** Separate the "AI Logic" (LangGraph nodes) from the "Django Views".