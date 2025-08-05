# Marketing Analysis AI Crew

This project uses CrewAI to automate marketing analysis for a given product or service. It assembles a team of AI agents to perform market research, competitor analysis, customer sentiment analysis, and synthesize the findings into a strategic report.

## Project Structure

```
/MarketMind/
├── main.py                 # Main script to run your crew
├── app.py                  # Streamlit UI to interact with the crew
├── tools/
│   ├── __init__.py
│   └── custom_search_tool.py # A custom tool for Reddit searches
├── config/
│   ├── agents.yaml           # Agent configurations
│   └── tasks.yaml            # Task configurations
├── .env                    # For storing API keys (create this from .env.example)
├── .env.example            # Example environment file
├── requirements.txt        # Project dependencies
└── README.md               # This file
```

## Setup and Installation

1.  **Clone the repository (or set up the project files as provided).**

2.  **Create a virtual environment and install dependencies:**
    It's recommended to use a virtual environment to manage project dependencies.

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables:**
    Create a `.env` file in the project root by copying the `.env.example` file.

    ```bash
    cp .env.example .env
    ```

    Now, edit the `.env` file to add your API keys:
    -   `OPENAI_API_KEY`: Your API key from OpenAI (or another LLM provider compatible with CrewAI).
    -   `SERPER_API_KEY`: Your API key from [Serper.dev](https://serper.dev) for the search tool.

## How to Run

There are two ways to run the marketing crew:

### 1. Via the Command Line

Execute the main script directly from your terminal:

```bash
python main.py
```

The crew will start its analysis using the default product name specified in `main.py` or the `PRODUCT_NAME` from your `.env` file. The final reports will be saved as Markdown files in the project root.

### 2. Via the Streamlit Web Interface

Launch the Streamlit application for an interactive experience:

```bash
streamlit run app.py
```

This will open a new tab in your web browser. You can configure the product name in the sidebar and click "Start Analysis" to kick off the crew. The real-time logs of the agents' work will be displayed on the page, and you can view and download the final reports once the process is complete.