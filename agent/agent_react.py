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
Create a new label for the authenticated user. Sublabels can be created using a '/' separator.
There will be an error if the label already exists.
The background color represented as hex string #RRGGBB (ex #000000). This field is required in order to set the color of a label. Only the following predefined set of color values are allowed:
#000000, #434343, #666666, #999999, #cccccc, #efefef, #f3f3f3, #ffffff, #fb4c2f, #ffad47, #fad165, #16a766, #43d692, #4a86e8, #a479e2, #f691b3, #f6c5be, #ffe6c7, #fef1d1, #b9e4d0, #c6f3de, #c9daf8, #e4d7f5, #fcdee8, #efa093, #ffd6a2, #fce8b3, #89d3b2, #a0eac9, #a4c2f4, #d0bcf1, #fbc8d9, #e66550, #ffbc6b, #fcda83, #44b984, #68dfa9, #6d9eeb, #b694e8, #f7a7c0, #cc3a21, #eaa041, #f2c960, #149e60, #3dc789, #3c78d8, #8e63ce, #e07798, #ac2b16, #cf8933, #d5ae49, #0b804b, #2a9c68, #285bac, #653e9b, #b65775, #822111, #a46a21, #aa8831, #076239, #1a764d, #1c4587, #41236d, #83334c #464646, #e7e7e7, #0d3472, #b6cff5, #0d3b44, #98d7e4, #3d188e, #e3d7ff, #711a36, #fbd3e0, #8a1c0a, #f2b2a8, #7a2e0b, #ffc8af, #7a4706, #ffdeb5, #594c05, #fbe983, #684e07, #fdedc1, #0b4f30, #b3efd3, #04502e, #a2dcc1, #c2c2c2, #4986e7, #2da2bb, #b99aff, #994a64, #f691b2, #ff7537, #ffad46, #662e37, #ebdbde, #cca6ac, #094228, #42d692, #16a765

delete_label:
e.g. delete_label: 'label_id'
Delete a label by its ID.
There will be an error if the label does not exist.

Example session:

Question: Create a label for my personal expenses.
Thought: I should list all labels using list_labels, if the label does not exist I will create it.
Action: list_labels: ""
PAUSE

You will be called again with this:

Observation: List of label resources if successful, None otherwise.

You then output:

Action: create_label: 'Expenses', '#FF0000'
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
        label_name = label_name.strip("'")  # Remove single quotes from label name
        if label_color:
            label_color = label_color.strip("'")  # Remove single quotes from label color
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
    "create_label": lambda inputs: create_label(*inputs.split(", ")),
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
        
question = "Delete my personal expenses label."
query(question)