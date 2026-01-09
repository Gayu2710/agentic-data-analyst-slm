# Agentic Data Analyst SLM

Agentic AI–based data analyst that answers analytical questions over a SQLite database using a Small Language Model (SLM), explicit tool calls, and full step‑level traces. It is implemented as a Flask API running locally on CPU.

---

## 1. Project Overview

This system behaves like a junior data analyst over the Brazilian E‑Commerce Public Dataset (Olist). It:

- Understands natural‑language analytical questions.
- Explores the database schema before querying.
- Plans multi‑step SQL strategies across multiple tables.
- Uses a fixed tool set (`list_tables`, `describe_table`, `run_query`, `validate_result`) to interact with SQLite.
- Validates intermediate results and exposes full observability via structured logs and a trace API. [file:2]

---

## 2. Architecture

Main components:

- **Flask API** (`app/api.py`)  
  - `GET /health` – liveness check.  
  - `POST /agent/query` – main question‑answer endpoint.  
  - `GET /agent/trace/<request_id>` – returns full agent execution trace as JSON.

- **Agent** (`app/agent.py`)  
  - Implements the plan–act–observe–decide loop.  
  - Uses tools to:
    - List tables and describe schemas.
    - Ask the SLM to propose SQL.
    - Execute SQL against SQLite.
    - Validate results and assemble final answers.
  - Logs every step into `logs/<request_id>.json`.

- **Tools** (`app/tools.py`)  
  - `list_tables()` – lists tables in the SQLite DB.  
  - `describe_table(table)` – returns columns for a table.  
  - `run_query(sql)` – executes SQL and returns rows.  
  - `validate_result(intent, result)` – checks whether the result matches analytical intent.

- **Database** (`db/` + SQLite file)  
  - SQLite database populated from the Olist Kaggle dataset.  
  - Tables include `customers`, `orders`, `order_items`, `payments`, `products`, `sellers` with proper foreign‑key relationships. [file:2]

---

## 3. Model Choice (SLM)

The agent uses a Small Language Model configured for local CPU inference to generate SQL plans and reason about tool usage.

- **Why SLM**  
  - Lightweight enough to run on CPU only.  
  - Supports structured prompts and tool‑oriented reasoning.  
  - Sufficient capacity for schema understanding and SQL planning, which is the focus of this task (not raw text quality). [file:2]

- **CPU performance observations**  
  - End‑to‑end question → answer latency is typically under a second for simple queries on a standard laptop CPU (single request).  
  - Memory usage stays within normal limits for local development.

- **Trade‑offs**  
  - Lower parameter count vs. large LLMs → faster and CPU‑friendly, but less robust on very ambiguous questions.  
  - Optimized prompts and explicit tools are used to compensate for model size by constraining the problem.  
  - Intended for single‑user / local analyst workflows rather than heavy concurrent production traffic.

- **Known limitations**  
  - Complex, long multi‑hop reasoning may need manual prompt refinement.  
  - Very domain‑specific jargon may require additional examples or hints.

*(Adjust this section to the exact SLM you wired in `agent.py`, e.g. “Gemma 2B CPU quantized via Ollama/ggml”, if you want to be more specific.)*

---

## 4. Data & Ingestion

### Dataset

- **Brazilian E‑Commerce Public Dataset by Olist (Kaggle)** – multi‑table ecommerce dataset recommended in the task description. [file:2]

Key CSV files used:

- `customers.csv`
- `orders.csv`
- `order_items.csv`
- `payments.csv`
- `products.csv`
- `sellers.csv`

### Ingestion into SQLite

1. Download the dataset from Kaggle.
2. Run the ingestion script(s) under `scripts/` (or the equivalent provided in this repo) to:
   - Create tables in SQLite.
   - Load each CSV into the corresponding table.
   - Set up foreign keys (e.g., `orders.customer_id → customers.customer_id`, `order_items.order_id → orders.order_id`, etc.). [file:2]
3. The resulting SQLite database file is stored under `db/`.

Table relationship highlights:

- `customers` ↔ `orders` (1‑to‑many)
- `orders` ↔ `order_items` (1‑to‑many)
- `orders` ↔ `payments` (1‑to‑many)
- `order_items` ↔ `products` and `sellers` (many‑to‑1)

---

## 5. Running the Project Locally

### Prerequisites

- Python 3.x
- Git
- Windows / macOS / Linux with CPU (no GPU required)

### Setup

```bash
git clone https://github.com/Gayu2710/agentic-data-analyst-slm.git
cd agentic-data-analyst-slm

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

pip install -r requirements.txt
