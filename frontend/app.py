from flask import Flask, render_template_string, request, redirect, url_for, session
import os, sys, yaml, time
from dotenv import load_dotenv, find_dotenv
import atexit

# Add the parent directory to the path so we can import from agent
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agent.agent_langgraph import Agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

# Load environment variables
_ = load_dotenv(find_dotenv())

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a secure secret key

def initialize_agent(checkpointer):
    # Load the prompt from YAML file
    with open(os.path.join(os.path.dirname(__file__), "../agent/prompts/agent_prompt.yaml"), "r") as f:
        config_yaml = yaml.safe_load(f)
    prompt = config_yaml.get("prompt", "")
    
    # Initialize the model
    gnai_key = os.getenv("GOOGLE_GEN_AI_KEY")
    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=gnai_key)
    
    agent = Agent(model, system=prompt, checkpointer=checkpointer)
    return agent

global_memory = MemorySaver()
global_agent = initialize_agent(global_memory)

# HTML template with revamped visuals
template = """
<!DOCTYPE html>
<html>
<head>
    <title>Gmail Agent Chat</title>
    <style>
        body { 
            font-family: 'Roboto', sans-serif; 
            background-color: #f3f4f6; 
            margin: 0; 
            padding: 0; 
            overflow-x: hidden;
        }
        .header { 
            background-color: #4A90E2; 
            color: white; 
            padding: 20px; 
            text-align: center; 
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .chat-container { 
            max-width: 800px; 
            margin: 20px auto; 
            padding: 20px; 
            background: #fff; 
            border: 1px solid #ddd; 
            height: 60vh; 
            overflow-y: auto; 
            border-radius: 10px; 
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .message { 
            margin: 10px 0; 
            padding: 10px; 
            border-radius: 10px; 
            max-width: 70%; 
            animation: fadeIn 0.3s ease-in-out;
        }
        .user { 
            background-color: #e6f7ff; 
            text-align: right; 
            margin-left: auto;
        }
        .agent { 
            background-color: #f0f0f0; 
            text-align: left; 
            margin-right: auto;
        }
        .input-container { 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 10px; 
            display: flex; 
            align-items: center; 
            justify-content: center;
        }
        .input-container form { 
            display: flex; 
            width: 100%;
        }
        .input-container input[type=text] { 
            flex: 1; 
            padding: 15px; 
            border: 1px solid #ccc; 
            border-radius: 25px; 
            font-size: 16px; 
            outline: none; 
            transition: border-color 0.3s;
        }
        .input-container input[type=text]:focus { 
            border-color: #4A90E2;
        }
        .input-container button { 
            padding: 15px 20px; 
            border: none; 
            background-color: #4A90E2; 
            color: white; 
            border-radius: 25px; 
            margin-left: 10px; 
            font-size: 16px; 
            cursor: pointer; 
            transition: background-color 0.3s;
        }
        .input-container button:hover { 
            background-color: #357ABD;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @media (max-width: 600px) {
            .chat-container { 
                height: 50vh; 
                padding: 15px;
            }
            .input-container input[type=text] { 
                font-size: 14px; 
                padding: 10px;
            }
            .input-container button { 
                font-size: 14px; 
                padding: 10px 15px;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Gmail Agent Chat</h1>
        <p>Ask me to help you manage your Gmail account.</p>
    </div>
    <div class="chat-container" id="chat-container">
        {% for msg in messages %}
            <div class="message {{ msg.type }}">
                {{ msg.content }}
            </div>
        {% endfor %}
    </div>
    <div class="input-container">
        <form method="post" action="/">
            <input type="text" name="user_input" placeholder="Type your message here..." autocomplete="off" required>
            <button type="submit">Send</button>
        </form>
    </div>
    <script>
        var chatContainer = document.getElementById("chat-container");
        chatContainer.scrollTop = chatContainer.scrollHeight;
    </script>
</body>
</html>
"""

@app.before_request
def make_session_permanent():
    # session.permanent line removed as per new requirement
    if "messages" not in session:
        session["messages"] = []

@app.route("/", methods=["GET", "POST"])
def chat():
    if "thread_id" not in session:
        session["thread_id"] = str(time.time())  # Persistent thread ID for session

    thread = {"configurable": {"thread_id": session["thread_id"]}}

    if request.method == "POST":
        user_input = request.form.get("user_input")
        if user_input:
            session.setdefault("messages", [])
            session["messages"].append({"type": "user", "content": user_input})

            # Pass full conversation history
            conversation_history = [
                HumanMessage(content=m["content"]) if m["type"] == "user" else AIMessage(content=m["content"])
                for m in session["messages"]
            ]

            for event in global_agent.graph.stream({"messages": conversation_history}, thread):
                for v in event.values():
                    msg = v["messages"][-1]
                    if isinstance(msg, AIMessage) and msg.content:
                        session["messages"].append({"type": "agent", "content": msg.content})

            return render_template_string(template, messages=session["messages"])
    else:
        # Initialize session messages on first load
        session["messages"] = []

        # Send an empty user message to get an initial response
        init_state = {"messages": [HumanMessage(content="")]}
        for event in global_agent.graph.stream(init_state, thread):
            for v in event.values():
                msg = v["messages"][-1]
                if isinstance(msg, AIMessage) and msg.content:
                    session["messages"].append({"type": "agent", "content": msg.content})

    return render_template_string(template, messages=session["messages"])


if __name__ == "__main__":
    app.run(debug=True)