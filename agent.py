from openai import AsyncOpenAI
from pydantic_ai import Agent 
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from core.config import api_key, base_url
from core.dependencies import AgentDeps
from core.schemas import AgentResponse
from tools.retrieve_rag_context import search_story_knowledge
from tools.web_tool import web_search

custom_client = AsyncOpenAI(
    base_url=base_url,
    api_key=api_key
)

# The 100% correct, docs-verified modern syntax
model = OpenAIChatModel(
    'gpt-4o-mini', 
    provider=OpenAIProvider(openai_client=custom_client)
)

story_agent = Agent(
    model=model,
    deps_type=AgentDeps,
    output_type=AgentResponse,
    system_prompt=(
        "You are an expert literary assistant specializing in the short story 'The Gift of the Magi'.\n"
        "Your primary directive is to answer user questions accurately, grounding your answers in facts.\n\n"
        "CORE Directives:\n"
        "1. PRIVATE KNOWLEDGE FIRST: If the user asks about the story's plot, characters, or quotes, you MUST use the `search_story_knowledge` tool.\n"
        "2. PUBLIC KNOWLEDGE: If the user asks about general world facts, the author's biography, or topics outside the story, use the `web_search` tool.\n"
        "3. NO HALLUCINATION: If your tools return no results, or if the circuit breaker trips, you must explicitly admit that you do not have the information.\n"
        "4. STRUCTURED OUTPUT: You must format your final answer strictly according to the required schema, providing both your textual answer and your confidence level."
    )
)

story_agent.tool(search_story_knowledge)
story_agent.tool_plain(web_search)