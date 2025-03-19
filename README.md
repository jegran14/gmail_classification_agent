# Gmail Classification Agent

## Objective

The objective of this project is to build an agent that, through natural language instructions, is able to classify emails, create filters, and labels in Gmail. The agent uses LLM technology to interpret user requests and perform actions on their Gmail account.

## Features

- List, create, delete, and update Gmail labels
- List, create, and delete Gmail filters
- Natural language interface for managing your email organization
- Customizable label colors
- Nested label support

## Technologies Used

- LangGraph for agent workflow management
- Google Gemini for natural language understanding
- Gmail API for interacting with Gmail accounts
- LangChain for connecting LLMs with tools

## Prerequisites

- Python 3.8 or later
- Google Cloud Platform account
- Gmail API credentials
- Google Generative AI API key

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/gmail_classification_agent.git
cd gmail_classification_agent
```

2. Install dependencies:
```
pip install -r requirements.txt
```

## Setting Up Gmail API Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API
4. Create OAuth 2.0 credentials
5. Download the credentials JSON file
6. Rename it to `credentials.json` and place it in a secure location

## Environment Variables

Create a `.env` file in the root directory of the project and add the following environment variables:

```
GOOGLE_GEN_AI_KEY="your_google_gen_ai_key"
GMAIL_CREDENTIALS_PATH="path_to_your_credentials.json"
GMAIL_TOKEN_PATH="path_to_your_token.json"
```

Replace `your_google_gen_ai_key`, `path_to_your_credentials.json`, and `path_to_your_token.json` with your actual values.

## Usage

Test the agent in terminal with:

```
python agent/agent_langgraph.py
```

Run the chatbot
```
python frontend/app.py
```

The agent will start an interactive session where you can type natural language commands like:

- "Create a new label called 'Important Work' with red color"
- "List all my current labels"
- "Create a filter that adds the 'Important Work' label to all emails from my boss"
- "Delete the label called 'Temporary'"

## Project Structure

```
gmail_classification_agent/
├── agent/
│   ├── utils/
│   │   ├── tools/
│   │   │   └── gmail_tools.py       # Gmail-related tools
│   │   ├── states/
│   │   │   └── base_state.py        # Agent state definitions
│   │   └── gmail_api/
│   │       └── gmail_api.py         # Gmail API wrapper
│   ├── prompts/
│   │   └── agent_prompt.yaml        # System prompts for the agent
│   └── agent_langgraph.py           # Main agent implementation
├── .env                             # Environment variables
└── README.md                        # This file
```

## License

[Include your license information here]

## Contributing

[Include contribution guidelines here]

