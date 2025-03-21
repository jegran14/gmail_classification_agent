import os
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())

from langchain_google_genai import ChatGoogleGenerativeAI # Import the ChatGoogleGenerativeAI classP from langchain_google_genai
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import ToolNode

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import yaml  # added import for YAML parsing

creds_path = os.getenv("GMAIL_CREDENTIALS_PATH")
token_path = os.getenv("GMAIL_TOKEN_PATH")

# region AGENT DEFINITION
from agent.utils.tools.gmail_tools import GmailToolkit
from agent.utils.states.base_state import AgentState
    

class Agent:
    def __init__(self, model, system = "", checkpointer = None):
        self.system = system
        graph = StateGraph(AgentState)  # Create a state graph with the AgentState class
        
        # Bind tools to the agent using GmailToolkit
        toolkit = GmailToolkit()
        tools = toolkit.get_tools()
        self.tool_node = ToolNode(tools)
        self.tools = {t.name: t for t in tools if hasattr(t, "name")}
        
        # Construct graph
        graph.add_node("execute", self.execute)
        graph.add_node("tools", self.tool_node)
        graph.add_conditional_edges(
            "execute",
            self.exists_action,
            {True: "tools", False: END}
        )
        graph.add_edge("tools", "execute")
        graph.set_entry_point("execute")
        
        # Compile the graph
        self.graph = graph.compile(checkpointer=checkpointer)
        self.model = model.bind_tools(self.tools.values())
        
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
        tool_calls = state["messages"][-1].tool_calls 
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
            

if __name__ == '__main__':
    # region TEST_AGENT
    with open(os.path.join(os.path.dirname(__file__), "prompts/agent_prompt.yaml"), "r") as f:
        config_yaml = yaml.safe_load(f)
    prompt = config_yaml.get("prompt", "")
    
    gnai_key = os.getenv("GOOGLE_GEN_AI_KEY")
    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=gnai_key)
    
    with SqliteSaver.from_conn_string(":memory:") as memory:
        agent = Agent(model, system=prompt, checkpointer=memory)
        thread = {"configurable": {"thread_id": "1"}}
        
        # Initial greeting from the agent
        init_state = {"messages": [HumanMessage(content="Hello what can you do?")]}
        for event in agent.graph.stream(init_state, thread):
            for v in event.values():
                msg = v["messages"][-1]
                if isinstance(msg, AIMessage) and msg.content:
                    print(f"Agent: {msg.content}")
        print("\n")
        
        while True:
            user_message = input("You: ")
            messages = [HumanMessage(content=user_message)]
            for event in agent.graph.stream({"messages": messages}, thread):
                for v in event.values():
                    msg = v["messages"][-1]
                    if isinstance(msg, AIMessage) and msg.content:
                        print(f"Agent: {msg.content}")
            print("\n")
    # endregion