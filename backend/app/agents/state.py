from typing import TypedDict, Annotated, List, Any
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    """
    State definition for the backend Orchestrator graph.
    
    Attributes:
        messages: A list of LangChain Message objects (HumanMessage, AIMessage, SystemMessage).
                  This preserves the conversation history and tool outputs.
    """
    messages: Annotated[List[BaseMessage], operator.add]
