from enum import Enum 
from pydantic import BaseModel, Field

class Confidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class AgentResponse(BaseModel):
    reasoning: str = Field(description='Internal reasoning process of the agent')
    action_taken: str = Field(description='Action taken by the agent based on the reasoning')
    answer: str = Field(description='Final answer or conclusion reached by the agent')
    confidence: Confidence = Field(description='Confidence level of the agent in its final answer')