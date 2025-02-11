from google import genai
import re
import os
from dotenv import load_dotenv
_ = load_dotenv()

# Start the client
genai_key = os.getenv("GOOGLE_GEN_AI_KEY")
client = genai.Client(api_key=genai_key)

""" # Generate response
response = client.models.generate_content(
    model = "gemini-2.0-flash",
    contents=["Say hello world and explain the different ways I can use the contents parameter from the generate_content function in the gnai library"]
)

print(response.text) """


class Agent:
    '''
    ReAct based agent from https://learn.deeplearning.ai/courses/ai-agents-in-langgraph/lesson/c1l2c/build-an-agent-from-scratch
    '''
    def __init__(self, system=""):
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
        chat = client.chats.create(model="gemini-2.0-flash")
        full_response = []  # Store response text
        # Combine all messages into a single input
        combined_message = "\n".join([message["content"] for message in self.messages])
        response = chat.send_message_stream(combined_message)
        for chunk in response:
            full_response.append(chunk.text)  # Store instead of printing
        
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

calculate:
e.g. calculate: 4 * 7 / 3
Runs a calculation and returns the number - uses Python so be sure to use floating point syntax if necessary

average_dog_weight:
e.g. average_dog_weight: Collie
returns average weight of a dog when given the breed

Example session:

Question: How much does a Bulldog weigh?
Thought: I should look the dogs weight using average_dog_weight
Action: average_dog_weight: Bulldog
PAUSE

You will be called again with this:

Observation: A Bulldog weights 51 lbs

You then output:

Answer: A bulldog weights 51 lbs
""".strip()

def calculate(what):
    return eval(what)

def average_dog_weight(name):
    if name in "Scottish Terrier":
        return ("Scottish Terriers average 20 is lbs")
    elif name in "Border Collie":
        return ("a Border Collies average weight is 37 lbs")
    elif name in "Toy Poodle":
        return ("A Toy Puddles average weight is 7 lbs")
    else:
        return ("An average dog weights 50 lbs")
    
known_actions = {
    "calculate": calculate,
    "average_dog_weight": average_dog_weight
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
        
question = """I have 2 dogs, a border collie and a scottish terrier. \
What is their combined weight"""
query(question)