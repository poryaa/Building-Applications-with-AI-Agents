# Structured Data Agent (Text-to-SQL + Text-to-Pandas)

An agentic “natural language data analyst” that takes user questions about a structured dataset, decides whether to generate SQL or Pandas, executes the code in a sandbox, inspects the result, and self-corrects when execution fails.

## Motivation

Text-to-SQL is one of the most in-demand enterprise agent patterns because it lets non-technical users query relational data with natural language instead of writing SQL by hand.  
This project extends that idea to both databases and flat files, routing between SQL and Pandas so the agent can work across typical analytics stacks (data warehouses, CSV exports, etc.).  

## What This Agent Does

- Accepts natural language questions about a structured dataset (industrial, financial, or any tabular data).  
- Chooses a backend:
  - **SQL**: when data lives in a database (SQLite/PostgreSQL).  
  - **Pandas**: when data is available as CSV/Parquet.  
- Generates SQL or Pandas code, executes it in a sandbox, and returns concise answers plus optional result samples.  
- Uses a **retry loop with self-correction**: inspects execution errors, updates the query/code, and retries before giving up.  

## Tech Stack

- **Core framework:** LangChain (agents, SQL tools, LLM orchestration).  
- **Agent graph / control flow:** LangGraph for routing, retries, and stateful workflows.  
- **Databases:** SQLite in dev; easily switchable to PostgreSQL in production.  
- **DataFrames:** Pandas for CSV/Parquet access and in-memory analytics.  
- **LLM:** Any LangChain-compatible chat model (OpenAI, Azure OpenAI, etc.).  
- **Observability & evaluation:** LangSmith for tracing, dataset-based evaluation, and execution accuracy tracking.  

## Target Resume Line

> Built a natural language data analyst agent with Text-to-SQL and self-correction; evaluated on the Spider benchmark achieving X% execution accuracy.

You can tune and update the **X%** after running LangSmith evaluations on Spider-style datasets or your own internal benchmarks.

## Architecture

At a high level, the system is a LangGraph agent with the following nodes:  

1. **Question intake & routing**
   - Normalize the user question and inspect metadata about available data sources (registered databases, CSVs, schemas).  
   - Use the LLM to decide whether to route to the **SQL agent** or the **Pandas agent**, with a fallback for ambiguous cases.  

2. **SQL agent (Text-to-SQL)**
   - Uses LangChain’s SQL toolkit / `create_sql_agent` to generate and execute SQL queries over the configured database.  
   - Leverages tools like `sql_db_list_tables`, `sql_db_schema`, and `sql_db_query` to inspect schema, generate safe SQL, and run queries with automatic correction.  

3. **Pandas agent (Text-to-Pandas)**
   - Loads CSV/Parquet into Pandas and builds DataFrame-based transformations from natural language instructions.  
   - Uses a constrained code-generation pattern, executing Pandas snippets in a restricted sandbox to prevent unsafe operations.  

4. **Self-correction and retry loop**
   - Wraps SQL and Pandas execution in a LangGraph node with retry policies: on errors, the agent sees the stack trace / error message and attempts to repair the query or code before retrying.  
   - After exhausting retries, returns a helpful failure message, including what was tried and how the question could be rephrased.  

5. **Answer synthesis**
   - Formats a natural language answer, optionally including:
     - Sample rows from the result.  
     - Aggregations / charts (if extended) and the underlying SQL or Pandas code for transparency.  

## Features

- **Unified natural language interface** for SQL databases and CSVs.  
- **Automatic routing** between Text-to-SQL and Text-to-Pandas based on question and data source.  
- **Schema-aware reasoning**: inspects table names, column types, and relationships before generating queries.  
- **Self-healing execution**: retries with refined queries/code on typical execution errors (syntax issues, missing columns, type mismatches).  
- **Strong observability** via LangSmith traces, including intermediate thoughts, tool calls, and query/code generations.  
- **Benchmarkable**: plug in Spider or custom datasets to measure execution and answer correctness over many queries.  

## Getting Started

### Prerequisites

- Python 3.10+  
- A virtual environment (recommended)  
- SQLite (for the built-in demo database); PostgreSQL optional for advanced setups  
- API key for your chosen LLM provider (e.g., `OPENAI_API_KEY`)  

### Installation

```bash
git clone <your-repo-url> structured-data-agent
cd structured-data-agent

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-...
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsm_...
DATABASE_URL=sqlite:///data/demo.db    # or postgres://user:pass@host:port/db
DATA_CSV_PATH=data/demo.csv            # path to your CSV for Pandas
```

The LangSmith keys are optional but recommended to get rich traces and evaluations.  

### Data Setup

- **SQL path:** Put a sample SQLite database (e.g., Chinook or an industrial/financial dataset) under `data/` and point `DATABASE_URL` to it.  
- **Pandas path:** Place one or more CSVs (e.g., transactions, sensor readings, KPIs) under `data/` and update `DATA_CSV_PATH`.  

## Running the Agent

### CLI Mode

```bash
python -m structured_agent.cli
```

Example questions:

- “What was the total revenue by year for the last 5 years?”  
- “List the top 10 customers by lifetime value.”  
- “For the CSV data, what’s the average downtime per machine per month?”  

The CLI prints:

- The final natural language answer.  
- The generated SQL or Pandas code (optional, controlled by a flag).  
- A small sample of the result rows if applicable.  

### Programmatic Usage

```python
from structured_agent.app import StructuredDataAgent

agent = StructuredDataAgent.from_env()
response = agent.ask("How many distinct customers do we have in Europe?")
print(response.answer)
print(response.backend)      # "sql" or "pandas"
print(response.code)         # generated SQL or Pandas snippet
print(response.sample_rows)  # optional preview of results
```

## Implementation Details

### Routing Logic

- The router inspects:
  - Available connections (which DBs are configured, what CSVs exist).  
  - Question hints (e.g., explicit “table”, “column” names vs “CSV” or “file”).  
- It calls an LLM with a routing prompt to decide whether to go to the SQL node or the Pandas node, and returns a structured decision (e.g., `"backend": "sql"`).  

### SQL Agent

- Built on top of LangChain’s `SQLDatabase` and related tools, or the `create_sql_agent` helper.  
- Pipeline:
  1. List tables and fetch relevant schemas.  
  2. Generate a syntactically correct query, using a checker tool to catch common SQL issues before execution.  
  3. Execute against SQLite/PostgreSQL with limits (`TOP_K`) to avoid huge result sets.  

### Pandas Agent

- Loads the target CSV/Parquet into a DataFrame at startup or on first use.  
- Given a question, asks the LLM to produce a small, **pure-Pandas** code snippet that:
  - Starts from a predefined `df`.  
  - Performs filters, group-bys, aggregations, joins, etc.  
- The snippet runs in a sandbox with:
  - No filesystem or network access.  
  - Time and resource limits.  

### Self-Correction with LangGraph

- The SQL and Pandas execution nodes are wrapped in a LangGraph node that includes a retry policy or manual retry loop.  
- On error:
  - The node captures the error message and recent query/code.  
  - Sends them back to the LLM with instructions to “fix the query/code and try again.”  
  - Retries up to `N` times before giving up.  

## Evaluation

- Use **LangSmith datasets** to evaluate the agent on:
  - Execution success rate (did the query/code run?).  
  - Answer correctness (does the returned answer match expected labels?).  
- For Text-to-SQL, you can adapt or subset the **Spider** benchmark for schema-rich, multi-table questions and report execution accuracy as a key metric.  

## Possible Extensions

- Add chart generation (e.g., Matplotlib/Plotly) for questions that naturally map to visualizations.  
- Integrate authentication and per-user access controls when pointing at production databases.  
- Support additional backends (DuckDB, BigQuery, Snowflake) and additional file formats (Excel).  
- Add a simple web UI (FastAPI + React/Next.js) to expose the agent to business users.  