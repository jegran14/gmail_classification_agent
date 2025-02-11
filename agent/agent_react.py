from google import genai
import re
import os
from dotenv import load_dotenv
_ = load_dotenv()

from typing import Optional

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from gmail_api.gmail_api import GmailAPI


# Start client
genai_key = os.getenv("GOOGLE_GEN_AI_KEY")
client = genai.Client(api_key=genai_key)

# Authenticate gmail of the user
creds_path = os.getenv("GMAIL_CREDENTIALS_PATH")
token_path = os.getenv("GMAIL_TOKEN_PATH")
gmail_api = GmailAPI(credentials_path=creds_path, token_path=token_path)
gmail_api()

class Agent:
    '''
    ReAct based agent from https://learn.deeplearning.ai/courses/ai-agents-in-langgraph/lesson/c1l2c/build-an-agent-from-scratch
    
    This goal for this agent is to be able to create or eliminate gmail filters and labels for mail classification based on user's instructions.
    '''
    
    def __init__(self, system=""):
        """
        Initialize a new instance of the class.

        This method sets up the initial state of the object with a system prompt
        and initializes the message history.

        Args:
            system (str, optional): The system prompt stablishes the agent behaviour.

        Attributes:
            system (str): Stores the system prompt that desribes the agent behaviour.
            messages (list): A list to store conversation messages, where each message
                is a dictionary containing 'role' and 'content' keys.
        """
        self.system = system
        self.messages = []
        if self.system:
            self.messages.append({"role": "system", "content": system})
            
            
    def __call__(self, message):
        self.messages.append({"role": "user", "content": message})
        result = self.execute()
        self.messages.append({"role": "assistant", "content": result})
        return result
    
    def execute(self):
        """
        Execute the agent's behaviour.
        """
        chat = client.chats.create(model="gemini-2.0-flash")
        full_response = []  # Store response text
        # Combine all messages into a single input
        combined_message = "\n".join([message["content"] for message in self.messages])
        response = chat.send_message_stream(combined_message)
        for chunk in response:
            full_response.append(chunk.text)
            
        # Join the collected response
        final_response = "".join(full_response)
        
        # Save the assistant response to message history
        self.messages.append({"role": "assistant", "content": final_response})
        
        return final_response  # Return the full response instead of printing it
    
    
prompt = """
You run in a loop of Thought, Action, PAUSE, Observation.
At the end of the loop you output an Answer
Use Thought to describe your thoughts about the question you have been asked.
Use Action to run one of the actions available to you - then return PAUSE.
Observation will be the result of running those actions.

Your available actions are:

list_labels:
e.g. list_labels
List all labels for the authenticated user.

create_label:
e.g. create_label: 'label_name', 'label_color' (optional)
Create a new label for the authenticated user.
There will be an error if the label already exists.

delete_label:
e.g. delete_label: 'label_id'
Delete a label by its ID.

Example session:

Question: Create a label for my personal expenses.
Thought: I should list all labels using list_labels, if the label does not exist I will create it.
Action: list_labels: ""
PAUSE

You will be called again with this:

Observation: List of label resources if successful, None otherwise.

You then output:

Answer: List of label resources if successful, None otherwise.
"""

def list_labels(void):
    """
    List all labels for the authenticated user.
    
    Returns:
        List of label resources if successful, None otherwise.
    """
    try:
        return gmail_api.list_labels()
    except Exception as error:
        print(f'An error occurred: {error}')
        return None
    
def create_label(label_name: str, label_color: Optional[str] = None):
    """
    Create a new label for the authenticated user.
    
    Args:
        label_name (str): The name of the label to create.
        label_color (str): The color of the label in hex format.
        
    Returns:
        Created label resource if successful, None otherwise.
    """
    try:
        return gmail_api.create_label(label_name, label_color)
    except Exception as error:
        print(f'An error occurred: {error}')
        return None
    
def delete_label(label_id: str):
    """
    Delete a label by its ID.
    
    Args:
        label_id (str): The ID of the label to delete.
    """
    try:
        label_id = label_id.strip("'")  # Remove single quotes from label ID
        print(f'Deleting label with ID: {label_id}')
        gmail_api.delete_label(label_id)
    except Exception as error:
        print(f'An error occurred: {error}')
        
def get_label_id(label_name: str):
    """
    Get the ID of a label by its name.
    
    Args:
        label_name (str): The name of the label to get the ID for.
        
    Returns:
        The ID of the label if found, None otherwise.
    """
    try:
        return gmail_api.get_label_id(label_name)
    except Exception as error:
        print(f'An error occurred: {error}')
        return None
    
known_actions = {
    "list_labels": list_labels,
    "create_label": create_label,
    "delete_label": delete_label,
    "get_label_id": get_label_id
}

action_re = re.compile(r'^Action: (\w+): (.*)$')   # python regular expression to selection action
def query(question, max_turns=5):
    i = 0
    bot = Agent(prompt)
    next_prompt = question
    while i < max_turns:
        i += 1
        result = bot(next_prompt)
        print(result)
        actions = [
            action_re.match(a)
            for a in result.split('\n')
            if action_re.match(a)
        ]
        
        if actions:
            # There is an action to run
            action, action_input = actions[0].groups()
            if action not in known_actions:
                raise Exception("Unkown action: {}: {}".format(action, action_input))
            print(" -- running {}: {}".format(action, action_input))
            observation = known_actions[action](action_input)
            print("Observation: ", observation)
            next_prompt = "Oberservation: {}".format(observation)
        else:
            return
        
question = "Eliminar la etiqueta de Facturas"
query(question)