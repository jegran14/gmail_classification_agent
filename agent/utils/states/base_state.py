from typing import TypedDict, Annotated, Dict, Optional, Union, List
from langchain_core.messages import AnyMessage
import operator


class AgentState(TypedDict):
    """
    Messages history of the agent. The Annotation operator.add is used to concatenate the list of messages.
    withouth the annotation, the list of messages would be replaced by the new list of messages.
    """
    messages: Annotated[list[AnyMessage], operator.add]