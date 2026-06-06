from dataclasses import dataclass 
from tools.RAG import RAGPipeline

@dataclass
class AgentDeps:
    """
    Holds all runtime dependencies for the ReAct Agent.
    Injected into tools via Pydantic AI's RunContext.
    """
    rag_pipeline: RAGPipeline
    rag_search_count: int = 0