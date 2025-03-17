from flask import Flask, render_template_string, request, redirect, url_for, session
import os, sys, yaml, time
from dotenv import load_dotenv, find_dotenv

# Add the parent directory to the path so we can import from agent
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agent.agent_langgraph import Agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver

# Load environment variables
_ = load_dotenv(find_dotenv())

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a secure secret key

def initialize_agent():
    # Load the prompt from YAML file
    with open(os.path.join(os.path.dirname(__file__), "../prompts/agent_prompt.yaml"), "r") as f:
        config_yaml = yaml.safe_load(f)
    prompt = config_yaml.get("prompt", "")
    
    # Initialize the model
    gnai_key = os.getenv("GOOGLE_GEN_AI_KEY")
    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=gnai_key)
    
    memory = MemorySaver()
    
    # Initialize the agent
    agent = Agent(model, system=prompt, checkpointer=memory)
    return agent

agent = initialize_agent()

# HTML template with revamped visuals
template = """
<!DOCTYPE html>
<html>
<head>
    <title>Gmail Agent Chat</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            background-color: #fdfdfd; 
            margin: 0; 
            padding: 0; 
            overflow-x: hidden;
        }
        .header { 
            background-color: #4A90E2; 
            color: white; 
            padding: 20px; 
            text-align: center; 
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
        }
        .message { 
            margin: 10px 0; 
            padding: 10px; 
            border-radius: 10px; 
            max-width: 70%;
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
        }
        .input-container form { 
            display: flex; 
        }
        .input-container input[type=text] { 
            flex: 1; 
            padding: 10px; 
            border: 1px solid #ccc; 
            border-radius: 5px; 
        }
        .input-container button { 
            padding: 10px; 
            border: none; 
            background-color: #4A90E2; 
            color: white; 
            border-radius: 5px; 
            margin-left: 10px; 
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
    if request.method == "POST":
        user_input = request.form.get("user_input")
        if user_input:
            session.setdefault("messages", [])
            session["messages"].append({"type": "user", "content": user_input})
            user_message = HumanMessage(content=user_input)
            # Get agent response (blocking call)
            for event in agent.graph.stream({"messages": [user_message]}, {"configurable": {"thread_id": str(time.time())}}):
                for v in event.values():
                    msg = v["messages"][-1]
                    if isinstance(msg, AIMessage) and msg.content:
                        session["messages"].append({"type": "agent", "content": msg.content})
            return render_template_string(template, messages=session["messages"])
    else:
        # Fresh chat: clear messages on every GET request
        session["messages"] = []
    return render_template_string(template, messages=session["messages"])

if __name__ == "__main__":
    app.run(debug=True)