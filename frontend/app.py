from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import os, sys, yaml, time, uuid
from dotenv import load_dotenv, find_dotenv
import markdown
import bleach
from bleach.sanitizer import ALLOWED_TAGS, ALLOWED_ATTRIBUTES
from typing import List

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

# Configure Markdown and Bleach for safe rendering
# Extended allowed tags for markdown rendering
EXTENDED_ALLOWED_TAGS = list(ALLOWED_TAGS) + [
    'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'pre', 'code',
    'ul', 'ol', 'li', 'blockquote', 'hr', 'br', 'strong', 
    'em', 'a', 'table', 'thead', 'tbody', 'tr', 'th', 'td'
]

# Extended attributes for links and code styling
EXTENDED_ALLOWED_ATTRIBUTES = dict(ALLOWED_ATTRIBUTES)
EXTENDED_ALLOWED_ATTRIBUTES['a'] = ['href', 'title', 'class']
EXTENDED_ALLOWED_ATTRIBUTES['code'] = ['class']
EXTENDED_ALLOWED_ATTRIBUTES['pre'] = ['class']

def process_markdown(text):
    """Convert markdown to HTML and sanitize"""
    # Convert markdown to HTML
    html = markdown.markdown(
        text, 
        extensions=['extra', 'codehilite', 'tables', 'fenced_code']
    )
    
    # Sanitize HTML to prevent XSS
    sanitized_html = bleach.clean(
        html,
        tags=EXTENDED_ALLOWED_TAGS,
        attributes=EXTENDED_ALLOWED_ATTRIBUTES,
        strip=True
    )
    
    return sanitized_html

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

# HTML template with modern design
template = """
<!DOCTYPE html>
<html>
<head>
    <title>Gmail Assistant</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/github.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js"></script>
    <style>
        :root {
            --primary-color: #1a73e8;
            --primary-light: #e8f0fe;
            --secondary-color: #5f6368;
            --background-color: #f8f9fa;
            --surface-color: #ffffff;
            --text-primary: #202124;
            --text-secondary: #5f6368;
            --border-color: #dadce0;
            --code-bg: #f5f7f9;
            --shadow-sm: 0 2px 5px rgba(0,0,0,0.08);
            --shadow-md: 0 4px 10px rgba(0,0,0,0.12);
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 24px;
            --transition: all 0.2s ease;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body { 
            font-family: 'Inter', sans-serif; 
            background-color: var(--background-color); 
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .header { 
            background-color: var(--surface-color); 
            padding: 16px 24px;
            box-shadow: var(--shadow-sm);
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo-container {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .logo {
            font-size: 24px;
            color: var(--primary-color);
        }
        
        .title-container h1 {
            font-size: 20px;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .title-container p {
            font-size: 14px;
            color: var(--text-secondary);
        }
        
        .actions {
            display: flex;
            gap: 12px;
        }
        
        .btn {
            padding: 10px 16px;
            border-radius: var(--radius-sm);
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: var(--transition);
            border: none;
            outline: none;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        
        .btn-primary {
            background-color: var(--primary-color);
            color: white;
        }
        
        .btn-primary:hover {
            background-color: #0b5cca;
        }
        
        .btn-secondary {
            background-color: var(--background-color);
            color: var(--primary-color);
            border: 1px solid var(--border-color);
        }
        
        .btn-secondary:hover {
            background-color: var(--primary-light);
        }
        
        .main-container {
            flex: 1;
            padding: 24px;
            display: flex;
            flex-direction: column;
            max-width: 900px;
            margin: 0 auto;
            width: 100%;
        }
        
        .chat-container { 
            flex: 1;
            background: var(--surface-color);
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-sm);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            margin-bottom: 24px;
            min-height: 60vh;
            max-height: 65vh;
        }
        
        .messages-container {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        
        .message { 
            padding: 12px 16px;
            border-radius: var(--radius-md);
            max-width: 80%;
            position: relative;
            animation: fadeIn 0.3s ease-in-out;
            line-height: 1.5;
            font-size: 15px;
            /* Add word breaking for long content */
            word-break: break-word;
            overflow-wrap: break-word;
        }
        
        .user { 
            background-color: var(--primary-light);
            color: var(--text-primary);
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }
        
        .agent { 
            background-color: var(--surface-color);
            color: var(--text-primary);
            align-self: flex-start;
            border: 1px solid var(--border-color);
            border-bottom-left-radius: 4px;
        }
        
        /* Markdown Styling */
        .agent h1, .agent h2, .agent h3, .agent h4, .agent h5, .agent h6 {
            margin-top: 16px;
            margin-bottom: 8px;
            font-weight: 600;
            line-height: 1.3;
        }
        
        .agent h1 { font-size: 1.6em; }
        .agent h2 { font-size: 1.4em; }
        .agent h3 { font-size: 1.2em; }
        
        .agent p {
            margin-bottom: 10px;
        }
        
        .agent ul, .agent ol {
            margin-bottom: 10px;
            margin-left: 20px;
        }
        
        .agent li {
            margin-bottom: 4px;
        }
        
        .agent pre {
            background-color: var(--code-bg);
            border-radius: var(--radius-sm);
            padding: 12px;
            margin: 10px 0;
            overflow-x: auto;
            /* Ensure code blocks handle long content properly */
            white-space: pre-wrap;
            word-break: break-all;
        }
        
        .agent code {
            font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
            font-size: 13px;
            background-color: var(--code-bg);
            padding: 2px 4px;
            border-radius: 3px;
            /* Handle long inline code */
            word-break: break-all;
        }
        
        .agent pre code {
            padding: 0;
            background-color: transparent;
        }
        
        .agent blockquote {
            border-left: 4px solid var(--primary-light);
            padding-left: 12px;
            margin: 10px 0;
            color: var(--text-secondary);
        }
        
        .agent a {
            color: var(--primary-color);
            text-decoration: none;
        }
        
        .agent a:hover {
            text-decoration: underline;
        }
        
        .agent table {
            border-collapse: collapse;
            margin: 10px 0;
            width: 100%;
        }
        
        .agent th, .agent td {
            border: 1px solid var(--border-color);
            padding: 8px;
            text-align: left;
        }
        
        .agent th {
            background-color: var(--background-color);
        }
        
        .input-container {
            padding: 16px;
            border-top: 1px solid var(--border-color);
            background-color: var(--surface-color);
            position: relative;
        }
        
        .input-container form { 
            display: flex;
            width: 100%;
            gap: 12px;
        }
        
        .input-container input[type=text] { 
            flex: 1; 
            padding: 12px 16px; 
            border: 1px solid var(--border-color); 
            border-radius: var(--radius-lg); 
            font-size: 15px; 
            outline: none; 
            transition: var(--transition);
            background-color: var(--background-color);
        }
        
        .input-container input[type=text]:focus { 
            border-color: var(--primary-color);
            box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.2);
        }
        
        .send-btn {
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: 50%;
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: var(--transition);
        }
        
        .send-btn:hover {
            background-color: #0b5cca;
        }
        
        .send-btn i {
            font-size: 18px;
        }
        
        .typing-indicator {
            display: flex;
            align-items: center;
            padding: 12px 16px;
            max-width: 80px;
            border-radius: var(--radius-md);
            background-color: var(--surface-color);
            border: 1px solid var(--border-color);
            align-self: flex-start;
            border-bottom-left-radius: 4px;
            margin-top: 8px;
        }
        
        .typing-dots {
            display: flex;
            gap: 4px;
        }
        
        .dot {
            width: 8px;
            height: 8px;
            background-color: var(--text-secondary);
            border-radius: 50%;
            opacity: 0.6;
            animation: pulse 1.5s infinite;
        }
        
        .dot:nth-child(2) {
            animation-delay: 0.5s;
        }
        
        .dot:nth-child(3) {
            animation-delay: 1s;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 0.6; transform: scale(1); }
            50% { opacity: 1; transform: scale(1.2); }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @media (max-width: 768px) {
            .header {
                padding: 12px 16px;
            }
            
            .title-container h1 {
                font-size: 18px;
            }
            
            .title-container p {
                display: none;
            }
            
            .main-container {
                padding: 16px;
            }
            
            .message {
                max-width: 90%;
                font-size: 14px;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo-container">
            <div class="logo"><i class="fas fa-robot"></i></div>
            <div class="title-container">
                <h1>Gmail Assistant</h1>
                <p>Your intelligent email companion</p>
            </div>
        </div>
        <div class="actions">
            <button id="clear-chat-btn" class="btn btn-secondary">
                <i class="fas fa-broom"></i> Clear Chat
            </button>
        </div>
    </div>
    
    <div class="main-container">
        <div id="chat-view" class="chat-container">
            <div id="messages-container" class="messages-container">
                {% for msg in messages %}
                    <div class="message {{ msg.type }}">
                        {% if msg.type == 'agent' %}
                            {{ msg.content|safe }}
                        {% else %}
                            {{ msg.content }}
                        {% endif %}
                    </div>
                {% endfor %}
            </div>
            <div class="input-container">
                <form id="chat-form" method="post" action="/">
                    <input type="text" name="user_input" id="user-input" placeholder="Type your message here..." autocomplete="off" required>
                    <button type="submit" class="send-btn">
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </form>
            </div>
        </div>
    </div>
    
    <script>
        // Initialize syntax highlighting
        document.addEventListener('DOMContentLoaded', (event) => {
            document.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightBlock(block);
            });
            
            // Initialize chat if no messages exist
            if (document.querySelectorAll('.message').length === 0) {
                initializeChat();
            }
        });
        
        // Function to highlight code in newly added messages
        function highlightNewCode() {
            document.querySelectorAll('pre code').forEach((block) => {
                if (!block.classList.contains('hljs')) {
                    hljs.highlightBlock(block);
                }
            });
        }
        
        // DOM elements
        const messagesContainer = document.getElementById("messages-container");
        const chatForm = document.getElementById("chat-form");
        const userInput = document.getElementById("user-input");
        const clearChatBtn = document.getElementById("clear-chat-btn");
        
        // Function to scroll to bottom of messages
        function scrollToBottom() {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        // Scroll to bottom on page load
        scrollToBottom();
        
        // Function to initialize chat
        function initializeChat() {
            // Add typing indicator
            const typingIndicator = document.createElement("div");
            typingIndicator.className = "typing-indicator";
            typingIndicator.innerHTML = '<div class="typing-dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>';
            messagesContainer.appendChild(typingIndicator);
            scrollToBottom();
            
            // Initialize chat with empty message
            fetch("/initialize", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                }
            })
            .then(response => response.json())
            .then(data => {
                // Remove typing indicator
                messagesContainer.removeChild(typingIndicator);
                
                // Add agent message
                const messageDiv = document.createElement("div");
                messageDiv.className = "message agent";
                messageDiv.innerHTML = data.message;
                messagesContainer.appendChild(messageDiv);
                
                // Apply syntax highlighting to code blocks
                highlightNewCode();
                scrollToBottom();
            });
        }
        
        // Clear chat button
        clearChatBtn.addEventListener("click", function() {
            fetch("/clear", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Clear messages
                    messagesContainer.innerHTML = "";
                    // Initialize a new chat
                    initializeChat();
                }
            });
        });
        
        // Handle chat form submission with AJAX
        chatForm.addEventListener("submit", function(e) {
            e.preventDefault();
            
            const userMessage = userInput.value.trim();
            if (!userMessage) return;
            
            // Add user message to chat
            const messageDiv = document.createElement("div");
            messageDiv.className = "message user";
            messageDiv.textContent = userMessage;
            messagesContainer.appendChild(messageDiv);
            scrollToBottom();
            
            // Clear input
            userInput.value = "";
            
            // Add typing indicator
            const typingIndicator = document.createElement("div");
            typingIndicator.className = "typing-indicator";
            typingIndicator.innerHTML = '<div class="typing-dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>';
            messagesContainer.appendChild(typingIndicator);
            scrollToBottom();
            
            // Send message to server
            fetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ user_input: userMessage })
            })
            .then(response => response.json())
            .then(data => {
                // Remove typing indicator
                messagesContainer.removeChild(typingIndicator);
                
                // Add agent message with HTML content
                const agentMessageDiv = document.createElement("div");
                agentMessageDiv.className = "message agent";
                agentMessageDiv.innerHTML = data.message;
                messagesContainer.appendChild(agentMessageDiv);
                
                // Apply syntax highlighting to code blocks
                highlightNewCode();
                scrollToBottom();
            });
        });
    </script>
</body>
</html>
"""

@app.before_request
def make_session_permanent():
    if "messages" not in session:
        session["messages"] = []

@app.route("/", methods=["GET"])
def chat():
    # Start a new chat on page refresh by clearing session data
    session["messages"] = []
    session["thread_id"] = str(uuid.uuid4())
    
    return render_template_string(template, messages=[])

@app.route("/initialize", methods=["POST"])
def initialize_chat():
    # Create a new thread ID
    session["thread_id"] = str(uuid.uuid4())
    session["messages"] = []
    
    # Create a new thread configuration
    thread = {"configurable": {"thread_id": session["thread_id"]}}
    
    # Send a greeting message instead of empty content
    init_state = {"messages": [HumanMessage(content="Hello, I need help with Gmail")]}
    agent_response = ""
    
    try:
        for event in global_agent.graph.stream(init_state, thread):
            for v in event.values():
                msg = v["messages"][-1]
                if isinstance(msg, AIMessage) and msg.content:
                    agent_response = msg.content
    except Exception as e:
        app.logger.error(f"Error during initialization: {str(e)}")
        agent_response = "I'm ready to help you with Gmail. What would you like to know or do today?"
    
    # Add to session messages
    if agent_response:
        session["messages"].append({"type": "agent", "content": agent_response})
    
    # Convert markdown to HTML for response
    html_response = process_markdown(agent_response) if agent_response else ""
    
    return jsonify({"success": True, "message": html_response})

@app.route("/chat", methods=["POST"])
def process_message():
    user_input = request.json.get("user_input")
    
    if not user_input:
        return jsonify({"success": False, "message": "No input provided"})
    
    # Add user message to session
    session["messages"].append({"type": "user", "content": user_input})
    
    # Get thread configuration
    thread = {"configurable": {"thread_id": session.get("thread_id", str(uuid.uuid4()))}}
    
    # Create conversation history
    conversation_history = [
        HumanMessage(content=m["content"]) if m["type"] == "user" else AIMessage(content=m["content"])
        for m in session["messages"]
    ]
    
    # Get agent response
    agent_response = ""
    try:
        for event in global_agent.graph.stream({"messages": conversation_history}, thread):
            for v in event.values():
                msg = v["messages"][-1]
                if isinstance(msg, AIMessage) and msg.content:
                    agent_response = msg.content
    except Exception as e:
        app.logger.error(f"Error during chat: {str(e)}")
        agent_response = "I encountered an error processing your request. Please try again."
    
    # Add agent response to session (store raw markdown)
    if agent_response:
        session["messages"].append({"type": "agent", "content": agent_response})
    
    # Convert markdown to HTML for response
    html_response = process_markdown(agent_response) if agent_response else ""
    
    return jsonify({"success": True, "message": html_response})

@app.route("/clear", methods=["POST"])
def clear_chat():
    # Clear session messages
    session["messages"] = []
    
    # Initialize a new agent (reinitialize)
    session["thread_id"] = str(uuid.uuid4())
    
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(debug=True)