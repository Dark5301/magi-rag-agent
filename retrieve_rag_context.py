from core.dependencies import AgentDeps
from pydantic_ai import RunContext
import logfire

async def search_story_knowledge(ctx: RunContext[AgentDeps], query: str) -> str:
    """
    Searches the internal vector database for semantic context about the story 'The Gift of the Magi'.

    WHEN TO USE:
    - Call this tool when the user asks specific questions about the story's plot, characters (like Della, Jim, or Mme. Sofronie), events, or themes.
    - Use this to fetch actual text from the document so you can ground your answer in facts rather than hallucinating.

    INPUT REQUIREMENTS:
    - The 'query' parameter should be a concise search phrase or keyword string extracted from the user's prompt (e.g., "Della hair cut", "Jim gold watch"). 
    - Do NOT pass conversational filler like "Can you tell me about..." into the query.

    WHEN NOT TO USE:
    - DO NOT use this tool for general world knowledge, math calculations, or current events.
    - DO NOT use this tool if the user is just saying "hello" or asking a meta-question about your instructions.
    """

    # 1. Observability: Open a span to track execution time and the exact query the LLM decided to use 
    with logfire.span('tool.search_story_knowledge', user_query=query) as span:
        # 2. READ THE BACKPACK: Has the agent used this too many times?
        if ctx.deps.rag_search_count >= 3:
            logfire.warning("Circuit breaker tripped! Stopping agent.")
            # We return a strict command to break the LLM out of its loop
            return (
                "SYSTEM OVERRIDE: You have searched the database 3 times. "
                "The information is explicitly NOT in this database. "
                "DO NOT search again. Tell the user you do not have the information."
            )
            
        # 3. UPDATE THE BACKPACK: The agent is safe to search, so we add 1.
        ctx.deps.rag_search_count += 1
        span.set_attribute("current_search_attempt", ctx.deps.rag_search_count)
        try:
            # 4. Dependency Injection: Grab the pipeline from the context 
            rag = ctx.deps.rag_pipeline

            # 5. Execution: Use the pipeline's own methods
            embedded_query = await rag.embedding([query])  # Embed the query
            results = rag.chunk_retrieval(embedded_query[0]['embedding'])

            # 6. Metric Tracking: Log how much text we are about to feed back into the LLM context window 
            span.set_attribute('retrieved_character_count', len(results))
            logfire.info('Successfully retrieved story context from Qdrant.')

            # Soft guardrail for empty results
            if not results or len(results.strip()) < 10:
                return "DATABASE RETURNED NO MATCHES. Try a different keyword, or stop searching."

            return results 
        except Exception as e:
            # 7. Graceful Degradation: If Qdrant or OpenAI goes down, catch the crash. 
            # We log the actual error for our dashboard, but return a simple string to the LLM.
            logfire.error('Database search failed inside tool.', error=str(e))
            return f'System Error: Could not retrieve information from the database at this time. Reason: {e}'