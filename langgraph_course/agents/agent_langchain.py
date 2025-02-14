import os
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())

from langchain_google_genai import ChatGoogleGenerativeAI # Import the ChatGoogleGenerativeAI class from langchain_google_genai
from langchain_core.tools.convert import tool # Import the tool function to convert a function  to tool
from typing import TypedDict, Annotated
import operator
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, END

# region TOOLS DEFINITION
@tool("calculate", parse_docstring=True)
def calculate(query: str) -> str:
    """Calculate the result of a mathematical expression.
    
    Args:
        query (str): The mathematical expression to calculate.
    """
    
    return eval(query)

@tool("average_dog_weight", parse_docstring=True)
def average_dog_weight(breed: str) -> str:
    """Search the average weight of a dog breed.
    
    Args:
        breed (str): The dog breed to calculate the average weight.
    """
    breed = breed.title()
    
    if breed in "Scottish Terrier":
        return ("Scottish Terrier average weight is 20 pounds.")
    elif breed in "Border Collie":
        return ("Border Collie average weight is 37 pounds.")
    elif breed in "Toy Poodle":
        return ("Toy Poodle average weight is 7 pounds.")
    else:
        return ("An average dog weights 50 pounds.")
# endregion

# region AGENT DEFINITION
class AgentState(TypedDict):
    """
    Messages history of the agent. The Annotation operator.add is used to concatenate the list of messages.
    withouth the annotation, the list of messages would be replaced by the new list of messages.
    """
    messages: Annotated[list[AnyMessage], operator.add]
    
    
class Agent:
    def __init__(self, model, tools, system = ""):
        self.system = system
        graph = StateGraph(AgentState) # Create a state graph with the AgentState class
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
        
        self.graph = graph.compile()
        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)
        
        
    def execute(self, state: AgentState):
        """
        Aexecute the agent with the user query
        """
        messages = state["messages"]
        if(self.system):
            messages = [SystemMessage(self.system)] + messages
        message = self.model.invoke(messages)
        return {'messages': [message]} # We only return the response and with Annotated from the Agent state and the add operator, we concatenate the new message to the list of messages.
    
    def take_action(self, state: AgentState):
        """
        Take action based on the llm response
        """
        tool_calls = state["messages"][-1].tool_calls # Get the tool calls from the last message
        results = []
        for t in tool_calls:
            print(f"Calling: {t}")  # Corrected string formatting
            if t['name'] not in self.tools:
                print(f"Unknown tool name: {t.name}")
                result = "Bad tool name, retry ......../n"
            else:
                result = self.tools[t['name']](t['args'])
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        return {'messages': results}
    
    def exists_action(self, state: AgentState):
        """
        Check if there is a tool call in the last message
        """
        return len(state["messages"][-1].tool_calls) > 0
    
    #endregion
    
    
# region TEST_AGENT
prompt = """
You are a super efficient dog breed weight calculator agent. \
You can take one or more actions before finishing the conversation.\
""".strip()

# Get genai key from the environment
genai_key = os.getenv("GOOGLE_GEN_AI_KEY")
# Create the langgraph model client
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=genai_key)
tools = [calculate, average_dog_weight]
bot = Agent(model, tools=tools, system=prompt)


question = """I have 2 dogs, a border collie and a scottish terrier. \
What is their combined weight"""
messages = [HumanMessage(content=question)]
result = bot.graph.invoke({"messages": messages})
print(result["messages"][-1].content)
#endregion