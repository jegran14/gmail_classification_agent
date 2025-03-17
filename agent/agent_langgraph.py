import os
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())

import operator
from typing import TypedDict, Annotated, Dict, Optional, Union, List
import uuid

from langchain_google_genai import ChatGoogleGenerativeAI # Import the ChatGoogleGenerativeAI class from langchain_google_genai
from langchain_core.tools.convert import tool # Import the tool function to convert a function  to tool
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from gmail_api.gmail_api import GmailAPI

import yaml  # added import for YAML parsing

creds_path = os.getenv("GMAIL_CREDENTIALS_PATH")
token_path = os.getenv("GMAIL_TOKEN_PATH")
gmail_api = GmailAPI(credentials_path=os.getenv("GMAIL_CREDENTIALS_PATH"), token_path=os.getenv("GMAIL_TOKEN_PATH"))
gmail_api()

#region TOOLS DEFINITION
#reguin LABELS
@tool
def list_labels() -> str:
    """List all the labels in the user's gmail account.
    
    Returns:
        A list of dictionaries containing the label information.
        {
            "id": string,
            "name": string,
            "messageListVisibility": enum (MessageListVisibility),
            "labelListVisibility": enum (LabelListVisibility),
            "type": enum (Type),
            "messagesTotal": integer,
            "messagesUnread": integer,
            "threadsTotal": integer,
            "threadsUnread": integer,
            "color": {
                object (Color)
            }
        }
    """
    labels = gmail_api.list_labels()
    
    if not labels:
        return "No labels found."
    
    return labels

@tool
def create_label(label_name: str, label_color: str) -> str:
    """Create a new label in the user's gmail account.
    
    Args:
        label_name (str): The name of the label to create. You can nest labels by using a '/' in the name. example ParentLabel/ChildLabel
        label_color (str): The color of the label in hex format.
            List of background available colors: #000000, #434343, #666666, #999999, #cccccc, #efefef, #f3f3f3, #ffffff, #fb4c2f, #ffad47, #fad165, #16a766, #43d692, #4a86e8, #a479e2, #f691b3, #f6c5be, #ffe6c7, #fef1d1, #b9e4d0, #c6f3de, #c9daf8, #e4d7f5, #fcdee8, #efa093, #ffd6a2, #fce8b3, #89d3b2, #a0eac9, #a4c2f4, #d0bcf1, #fbc8d9, #e66550, #ffbc6b, #fcda83, #44b984, #68dfa9, #6d9eeb, #b694e8, #f7a7c0, #cc3a21, #eaa041, #f2c960, #149e60, #3dc789, #3c78d8, #8e63ce, #e07798, #ac2b16, #cf8933, #d5ae49, #0b804b, #2a9c68, #285bac, #653e9b, #b65775, #822111, #a46a21, #aa8831, #076239, #1a764d, #1c4587, #41236d, #83334c #464646, #e7e7e7, #0d3472, #b6cff5, #0d3b44, #98d7e4, #3d188e, #e3d7ff, #711a36, #fbd3e0, #8a1c0a, #f2b2a8, #7a2e0b, #ffc8af, #7a4706, #ffdeb5, #594c05, #fbe983, #684e07, #fdedc1, #0b4f30, #b3efd3, #04502e, #a2dcc1, #c2c2c2, #4986e7, #2da2bb, #b99aff, #994a64, #f691b2, #ff7537, #ffad46, #662e37, #ebdbde, #cca6ac, #094228, #42d692, #16a765
        
    Returns:
        A message indicating the success or failure of the label creation
    """
    label = gmail_api.create_label(label_name, label_color)
    
    if not label:
        return "Label could not be created."
    
    return f"Label {label['name']} created successfully."

@tool
def delete_label(label_id: str) -> str:
    """Delete a label from the user's gmail account.
    
    Args:
        label_id (str): The ID of the label to delete.
        
    Returns:
        A message indicating the success or failure of the label deletion
    """
    try:
        gmail_api.delete_label(label_id)
        return f"Label with ID {label_id} deleted successfully."
    except Exception as error:
        return f"An error occurred: {error}"   

@tool
def update_label(label_id: str, new_name: Optional[str] = None, new_color: Optional[str] = None) -> str:
    """Update an existing label in the user's gmail account.
    
    Args:
        label_id (str): The ID of the label to update.
        new_name (str): The new name for the label.
        new_color (str): The new color for the label in hex format.
        
    Returns:
        A message indicating the success or failure of the label update.
    """
    label = gmail_api.update_label(label_id, new_name, new_color)
    
    if not label:
        return "Label could not be updated."
    
    return f"Label {label['name']} updated successfully."
#endregion 
    
#region FILTERS
@tool 
def list_filters(self):
    """List all the filters in the user's gmail account.
    
    Returns:
        A list of dictionaries containing the filter information.
        {
            "id": string,
            "criteria": {
                object (FilterCriteria)
            },
            "action": {
                object (FilterAction)
            }
        }
    """
    return gmail_api.list_filters()

@tool
def create_filter(criteria: Dict[str, str], actions: Dict[str, Union[str, List[str]]]) -> str:
    """Create a new filter in the user's gmail account.
    
    Args:
        criteria (Dict[str, str]): Filter criteria dictionary with possible keys:
                - from: Sender email
                - to: Recipient email
                - subject: Email subject
                - query: Gmail search query
        actions (Dict[str, Union[str, List[str]]]): Filter actions dictionary with possible keys:
            - addLabelIds: List of label IDs to add to the matching messages. Can only have one user defined label.
            - removeLabelIds: List of label IDs to remove from the matching messages.
            - forward: Email address to forward the matching messages to.

    Example:
    label_id_toAdd = "IMPORTANT" # User defined labels need to be passed by their id
    label_id_toRemove = "INBOX"
    filter_content = {
        "criteria": {"from": "gsuder1@workspacesamples.dev"},
        "action": {
            "addLabelIds": [label_id],
            "removeLabelIds": ["label_id"],
        },
    }
    """
    print(f"Criteria: {criteria}")
    print(f"Actions: {actions}")

    # Ensure addLabelIds and removeLabelIds are strings
    if 'addLabelIds' in actions and isinstance(actions['addLabelIds'], list):
        actions['addLabelIds'] = ','.join(actions['addLabelIds'])
    if 'removeLabelIds' in actions and isinstance(actions['removeLabelIds'], list):
        actions['removeLabelIds'] = ','.join(actions['removeLabelIds'])
    
    return gmail_api.create_filter(criteria, actions)
# endregion

@tool
def human_assistance(query: str) -> str:
    """
    Request human assistance for clarification or confirmation
    
    Args:
        query (str): The query that requires human assistance.
    """

    user_input = input(f"{query}\n")
    return user_input

#tools = [list_labels, create_label, delete_label]
tools = [list_labels, create_label, delete_label, update_label]
#endregion

# region AGENT DEFINITION
from langgraph.types import interrupt

class AgentState(TypedDict):
    """
    Messages history of the agent. The Annotation operator.add is used to concatenate the list of messages.
    withouth the annotation, the list of messages would be replaced by the new list of messages.
    """
    messages: Annotated[list[AnyMessage], operator.add]
    

class Agent:
    def __init__(self, model, tools, system = "", checkpointer = None):
        self.system = system
        graph = StateGraph(AgentState)  # Create a state graph with the AgentState class
        # Construct graph
        graph.add_node("execute", self.execute)
        graph.add_node("action", self.take_action)
        graph.add_conditional_edges(
            "execute",
            self.exists_action,
            {True: "action", False: END}
        )
        graph.add_edge("action", "execute")
        graph.set_entry_point("execute")
        
        # Compile the graph
        self.graph = graph.compile(checkpointer=checkpointer)
        
        # Bind tools to the agent
        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)
        
    def execute(self, state: AgentState):
        """
        Aexecute the agent with the user query
        """
        messages = state["messages"]
        if(self.system):
            messages = [SystemMessage(content=self.system)] + messages
        message = self.model.invoke(messages)
        return {'messages': [message]}
    

    def take_action(self, state: AgentState):
        """
        Take an action based on the user query.
        Only execute tool calls that were confirmed.
        """
        tool_calls = state["messages"][-1].tool_calls  # tool_calls already filtered by ask_human
        results = []
        for t in tool_calls:
            print(f"Calling: {t}")
            if t['name'] not in self.tools:
                print(f"Unknown tool name: {t['name']}")
                result = "Bad tool name, retry ......../n"
            else:
                result = self.tools[t['name']].invoke(t['args'])
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        return {'messages': results}

    def exists_action(self, state: AgentState):
        """
        Check if there is a tool call in the last message
        """
        return len(state["messages"][-1].tool_calls) > 0
# endregion

# region TEST_AGENT
# Load prompt from the YAML file using a relative path
with open(os.path.join(os.path.dirname(__file__), "../prompts/agent_prompt.yaml"), "r") as f:
    config_yaml = yaml.safe_load(f)
prompt = config_yaml.get("prompt", "")

gnai_key = os.getenv("GOOGLE_GEN_AI_KEY")
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=gnai_key)

# Using the checkpointer within a context to ensure it’s properly constructed
with SqliteSaver.from_conn_string(":memory:") as memory:
    agent = Agent(model, tools, system=prompt, checkpointer=memory)
    question = "I want to delete on of the labels but don't know which ones I have"
    messages = [HumanMessage(content=question)]
    thread = {"configurable": {"thread_id": "1"}}
    for event in agent.graph.stream({"messages": messages}, thread):
        for v in event.values():
            print(v)
# endregion