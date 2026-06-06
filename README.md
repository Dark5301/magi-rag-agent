# 📖 The Gift of the Magi — Conversational RAG Agent

A production-grade conversational AI agent built with **PydanticAI**, **Qdrant Cloud**, and **LogFire** that answers questions about O. Henry's *The Gift of the Magi*. The agent intelligently routes queries between a private vector database and live web search, with structured outputs, circuit-breaker protection, and full observability.

---

## ✨ Features

- **Dual-tool routing** — Automatically selects between a private RAG knowledge base (story-specific queries) and DuckDuckGo web search (general/biographical queries)
- **Structured output** — Every response is validated against a Pydantic schema, returning the answer, internal reasoning, action taken, and a confidence level
- **Circuit breaker** — Prevents infinite tool-call loops by capping RAG searches at 3 per turn
- **Multi-turn conversation** — Full message history is maintained across turns via PydanticAI's `message_history` API
- **Production observability** — Every span, tool call, and metric is instrumented with LogFire
- **Deterministic chunk deduplication** — MD5-based UUIDs ensure idempotent upserts into Qdrant

---

## 🏗️ Architecture

```
main.py (CLIOrchestrator)
    │
    ├── Startup: RAGPipeline initialised once, connection verified
    │
    └── Per-turn: handle_turn()
            │
            ├── AgentDeps minted fresh (rag_pipeline + rag_search_count)
            │
            └── story_agent.run()
                    │
                    ├── Tool: search_story_knowledge  ──► RAGPipeline.embedding()
                    │                                         └──► RAGPipeline.chunk_retrieval() ──► Qdrant Cloud
                    │
                    └── Tool: web_search  ──► DuckDuckGo (ddgs)
```

**Data flow for ingestion (run once):**
```
rag_text.txt ──► load_documents() ──► chunk_document() ──► embedding() ──► store_embeddings() ──► Qdrant Cloud
```

---

## 📁 Project Structure

```
.
├── agent.py                    # Agent definition, model config, tool registration
├── main.py                     # CLIOrchestrator — startup, interaction loop, telemetry
├── core/
│   ├── config.py               # Environment loading, LogFire boot, key validation
│   ├── dependencies.py         # AgentDeps dataclass (injected into tools via RunContext)
│   └── schemas.py              # AgentResponse + Confidence Pydantic models
└── tools/
    ├── RAG.py                  # RAGPipeline — ingestion, embedding, and retrieval
    ├── retrieve_rag_context.py # search_story_knowledge tool (with circuit breaker)
    └── web_tool.py             # web_search tool (DuckDuckGo via ddgs)
```

---

## ⚙️ Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/Dark5301/magi-rag-agent
cd magi-rag-agent
```

### 2. Configure environment variables

Create a `.env` file in the project root:

```env
AICREDITS_API_KEY=your_aicredits_api_key
AICREDITS_URL=https://api.aicredits.in/v1
QDRANT_URL=your_qdrant_cloud_cluster_url
QDRANT_API_KEY=your_qdrant_api_key
```

### 3. Run ingestion (one-time only)

Download `rag_text.txt` (the Project Gutenberg edition of *The Gift of the Magi*), update the filepath in `RAG.py`, then run:

```bash
python3 RAG.py
```

This will chunk the story, generate embeddings, and upsert all vectors into your Qdrant Cloud collection. **Do not re-run this** unless you want to repopulate the collection.

### 4. Start the agent

```bash
python3 main.py
```

---

## 💬 Example Session

```
System Online! You are now talking to the "Gift of the Magi" Agent.
Type 'quit' or 'exit' to shut down.
--------------------------------------------------

You: What exactly did Della sell to buy Jim's gift, and how much money did she receive for it?

========================================
🛠️  TOOL UTILIZED : Aggregated found information about Della's actions
🧠 AGENT REASONING: Found relevant information about what Della sold and the amount received.
📊 CONFIDENCE     : medium/10
========================================

Agent:
Della sold her long hair to buy Jim a present and received $20 for it.

You: I know O. Henry wrote this story, but what was his actual birth name and what year was he born?

========================================
🛠️  TOOL UTILIZED : Cited information about O. Henry's birth name and year of birth.
🧠 AGENT REASONING: Found information from reliable web sources.
📊 CONFIDENCE     : high/10
========================================

Agent:
O. Henry's actual birth name was William Sidney Porter, and he was born on September 11, 1862.
```

---

## 🔧 Key Design Decisions

### Tool Routing Strategy
The agent's system prompt establishes a clear hierarchy: story-specific questions go to `search_story_knowledge` (private RAG), while biographical or general knowledge questions go to `web_search`. The LLM resolves hybrid queries (e.g., comparing a story price to a real-world price) by calling **both tools in parallel**.

### Circuit Breaker
`AgentDeps.rag_search_count` is incremented on every RAG tool call. Once it hits 3, the tool returns a `SYSTEM OVERRIDE` string that instructs the LLM to stop searching and admit it does not have the information — preventing runaway loops and unnecessary API spend.

### Deterministic Chunk IDs
Each chunk is hashed with MD5 and converted to a UUID. This ensures that re-running ingestion never creates duplicate points in Qdrant — every `upsert` is fully idempotent.

### Dependency Injection per Turn
A fresh `AgentDeps` instance is minted at the start of every `handle_turn()` call. This resets `rag_search_count` to `0` between turns while sharing the same persistent `RAGPipeline` connection across the session's lifetime.

### Message History
`result.new_messages()` is captured after each turn and passed into the next `agent.run()` call as `message_history`, giving the agent full conversational context without managing raw message objects manually.

---

## 📊 Observability

All critical operations are wrapped in LogFire spans:

| Span | Tracked Attributes |
|---|---|
| `orchestrator.startup` | Boot success/failure |
| `orchestrator.chat_turn` | `user_input`, `agent_confidence`, `tool_selection` |
| `tool.search_story_knowledge` | `user_query`, `current_search_attempt`, `retrieved_character_count` |
| `tool.web_search` | `search_query`, `results_count` |
| `rag.generate_embeddings` | `batch_size`, `tokens_used` |
| `rag.retrieve_context` | `retrieved_chunks` |
| `rag.full_ingestion_pipeline` | Full ingestion lifecycle |

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Agent framework | [PydanticAI](https://ai.pydantic.dev) |
| LLM | `gpt-4o-mini` via [aicredits.in](https://aicredits.in) (OpenAI-compatible) |
| Vector database | [Qdrant Cloud](https://qdrant.tech) |
| Embeddings | `text-embedding-3-small` (1536 dimensions, cosine similarity) |
| Web search | [ddgs](https://pypi.org/project/ddgs/) (DuckDuckGo) |
| Observability | [LogFire](https://logfire.pydantic.dev) |
| Validation | [Pydantic v2](https://docs.pydantic.dev) |

---

## 📄 License

MIT
