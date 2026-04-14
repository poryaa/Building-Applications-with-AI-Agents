# 🔬 Project 3 — Tool-Augmented Research Agent with Memory

> A self-critiquing, memory-aware research assistant powered by LangGraph, Tavily, and LangSmith.

---

## 📌 Overview

This agent takes a user query and autonomously:

1. **Searches the web** via [Tavily](https://tavily.com/) for relevant, up-to-date sources
2. **Reads & summarizes** specific URLs for deeper content extraction
3. **Stores findings** in both short-term conversation memory (LangGraph state) and long-term memory (vector store or external DB)
4. **Produces a structured report** with cited sources and organized sections
5. **Reflects & rewrites** — a dedicated Reflection node critiques the draft and rewrites weak or hallucinated sections

---

## 🧠 Why It Matters

Reflection is a core agentic pattern — covered in depth in **Learning LangChain, Chapter 7 (Agents II — Reflection)**.

This project directly extends the **Report Writer Agent (Project 2.4)** by layering on:

- ✅ **Persistent memory** across sessions (long-term vector store)
- ✅ **Self-critique loop** to reduce hallucinations through agent debate/reflection
- ✅ **LangSmith tracing** for full observability and eval

> 💼 Hiring managers in 2026 specifically look for agents that *"reduce hallucinations through debate/reflection"* — this project directly addresses that signal.

---

## 🏗️ Architecture

```
User Query
    │
    ▼
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐
│  Web Search  │────▶│  URL Reader  │────▶│  Report Drafter  │
│  (Tavily)    │     │ (Summarizer) │     │  (LangGraph)     │
└─────────────┘     └──────────────┘     └────────┬─────────┘
                                                   │
                          ┌────────────────────────▼──────────────────────────┐
                          │              Reflection Node                       │
                          │  • Critiques draft for gaps, hallucinations, bias  │
                          │  • Rewrites weak sections                          │
                          └────────────────────────┬──────────────────────────┘
                                                   │
                    ┌──────────────────────────────▼──────────────────┐
                    │                Final Structured Report            │
                    │  (stored in short-term state + long-term memory) │
                    └─────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Tool |
|---|---|
| Agent Framework | [LangGraph](https://github.com/langchain-ai/langgraph) (ReAct + Reflection node) |
| Web Search | [Tavily Search API](https://tavily.com/) |
| Observability & Eval | [LangSmith](https://smith.langchain.com/) |
| Long-term Memory | [Redis](https://redis.io/) or [Chroma](https://www.trychroma.com/) |
| Short-term Memory | LangGraph State (conversation history) |

---

## 🚀 Getting Started

### Prerequisites

```bash
pip install langgraph langchain langchain-community tavily-python langsmith chromadb
```

### Environment Variables

```bash
export TAVILY_API_KEY="your_tavily_key"
export LANGCHAIN_API_KEY="your_langsmith_key"
export LANGCHAIN_TRACING_V2="true"
export LANGCHAIN_PROJECT="research-agent-project3"
```

### Run the Agent

```bash
python main.py --query "What are the latest trends in agentic AI for 2026?"
```

---

## 🔄 Agent Flow

```
[ReAct Node] → search/read tools → [Draft Report] → [Reflection Node] → [Rewrite] → [Final Output]
       ↑__________________________feedback loop if reflection score < threshold_____|
```

The **Reflection node** evaluates the draft against criteria such as:

- Source coverage and citation accuracy
- Logical coherence and factual consistency
- Section completeness and clarity

If quality thresholds are not met, the agent loops back and improves the report.

---

## 📊 Evaluation (LangSmith)

Tracks the following metrics per run:

- **Hallucination Rate** — verified against source documents
- **Citation Accuracy** — % of claims backed by retrieved sources
- **Reflection Loop Count** — number of critique-rewrite iterations
- **Latency** — end-to-end query-to-report time

---

## 📄 Resume Signal

> *"Extended ReAct agent with a Reflection-Critique loop; demonstrated measurable reduction in hallucination rate on a custom eval dataset using LangSmith."*

---

## 🔗 Related Projects

- **Project 2.4** — Report Writer Agent *(base architecture this project extends)*
- **Project 4** *(coming soon)* — Multi-Agent Collaboration with LangGraph

---

## 📚 References

- [Learning LangChain — Chapter 7: Agents II (Reflection)](https://www.oreilly.com/library/view/learning-langchain/9781098167264/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Tavily Search API](https://tavily.com/)
- [LangSmith Tracing & Evaluation](https://smith.langchain.com/)