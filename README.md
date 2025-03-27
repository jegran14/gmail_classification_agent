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
```bash
git clone https://github.com/yourusername/gmail_classification_agent.git
cd gmail_classification_agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Setting Up Gmail API Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services > Library** and search for "Gmail API"
4. Click on Gmail API and then **Enable**
5. Go to **APIs & Services > Credentials**
6. Click **Create Credentials** and select **OAuth client ID**
7. Select **Desktop app** as the application type, give it a name, and click **Create**
8. Download the JSON file, rename it to `credentials.json` and place it in the `gmail_api/utils/` directory

## Setting Up Google Gemini API

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key or use an existing one
3. Copy the API key for use in your environment variables

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

Run the chatbot with
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
│   │   │   └── gmail_tools.py       # Gmail-related toolset
│   │   └── states/
│   │       └── base_state.py        # Agent state definitions
│   ├── prompts/
│   │   └── agent_prompt.yaml        # System prompts for the agent
│   └── agent_langgraph.py           # Main agent implementation
├── frontend/
│   └── app.py                       # Flask web interface
├── gmail_api/
│   ├── utils/
│   │   └── token.json               # Authentication token storage
│   └── gmail_api.py                 # Gmail API wrapper
├── requirements.txt                 # Project dependencies
├── .env                             # Environment variables
├── .gitignore                       # Git ignore file
└── README.md                        # Project documentation
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/gmail_classification_agent.git`
3. Create a new branch for your feature: `git checkout -b feature/feature-name`
4. Make your changes
5. Run tests to ensure everything works as expected
6. Commit your changes: `git commit -m "Add some feature"`
7. Push to your branch: `git push origin feature/feature-name`
8. Submit a pull request


### Reporting Issues

If you find a bug or have a suggestion for improvement:

1. Check if the issue already exists in the Issues section
2. If not, create a new issue with a descriptive title and detailed information
3. Include steps to reproduce, expected behavior, and actual behavior
4. Add relevant screenshots or error logs if applicable

We appreciate all contributions and will review them as quickly as possible!