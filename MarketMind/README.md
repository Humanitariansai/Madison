# 🚀 MarketMinds - Multi-Agent AI Market Research Crew

A sophisticated multi-agent AI crew that conducts comprehensive market research like a team of expert consultants, but faster and smarter.

## 🌟 What Makes This Special?

**MarketMinds** isn't just another market research tool - it's a collaborative AI crew where each agent has a specific expertise and personality. Think of it as having a dream team of consultants working together 24/7:

### 🤖 The AI Crew

| Agent | Role | Personality | What They Do |
|-------|------|-------------|--------------|
| **Strategy Consultant** | Research Framing | Seasoned McKinsey consultant | Asks the right questions to guide the entire research process |
| **Competitor Analyst** | Competitive Intelligence | Meticulous analyst with strong opinions | Deep-dives into competitors with real-time data and scoring |
| **Customer Persona Analyst** | User Segmentation | Empathetic storyteller | Creates vivid, data-driven user personas |
| **Devil's Advocate** | Critical Evaluation | Brutally honest skeptic | Stress-tests findings and challenges assumptions |
| **Lead Strategy Synthesizer** | Final Synthesis | Strategic visionary | Turns all insights into actionable strategies |

## 🎯 Key Features

- **Real-time Market Analysis**: Get comprehensive competitive intelligence in minutes, not months
- **Multi-Agent Collaboration**: Specialized AI agents working together for deeper insights
- **Evidence-Based Scoring**: Detailed rubrics with specific data points and sources
- **Interactive Web Interface**: Beautiful Streamlit UI for easy interaction
- **Comprehensive Reports**: Detailed markdown reports ready for stakeholders
- **Customizable Research**: Focus on specific competitors, industries, or geographies

## 🚀 Complete Setup Guide

### Prerequisites
- **Python 3.8 or higher** (check with `python --version`)
- **Git** (for cloning) or ability to download ZIP files
- **OpenAI API key** (get from [OpenAI Platform](https://platform.openai.com/api-keys))
- **Serper API key** (get from [Serper.dev](https://serper.dev) for web search capabilities)

### Step 1: Get the Code

#### Option A: Fork and Clone (Recommended for contributors)
```bash
# Fork the repository on GitHub first, then:
git clone https://github.com/YOUR_USERNAME/MarketMinds.git
cd MarketMinds
```

#### Option B: Download ZIP
1. Click the green "Code" button on GitHub
2. Select "Download ZIP"
3. Extract the ZIP file to your desired location
4. Open terminal/command prompt in the extracted folder

### Step 2: Set Up Python Environment

#### Create Virtual Environment
```bash
# On macOS/Linux:
python3 -m venv venv
source venv/bin/activate

# On Windows:
python -m venv venv
venv\Scripts\activate

# On Windows (if the above doesn't work):
python -m venv venv
.\venv\Scripts\activate
```

#### Install Dependencies
```bash
# Upgrade pip first (recommended)
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

### Step 3: Configure API Keys

#### Create Environment File
```bash
# Copy the example environment file
cp .env.example .env
```

#### Edit the .env File
Open the `.env` file in your preferred text editor and add your API keys:

```bash
# .env file contents:
OPENAI_API_KEY=your_openai_api_key_here
SERPER_API_KEY=your_serper_api_key_here
PRODUCT_NAME=Your Product Name
PRODUCT_DESCRIPTION=Your product description
INDUSTRY=Your target industry
GEOGRAPHY=Your target geography
SCALE=Your company scale
```

**Important Notes:**
- Replace `your_openai_api_key_here` with your actual OpenAI API key
- Replace `your_serper_api_key_here` with your actual Serper API key
- The other variables are optional and can be set via the web interface
- Never commit your `.env` file to version control (it's already in `.gitignore`)

### Step 4: Get Your API Keys

#### OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key and paste it in your `.env` file
5. **Important**: Keep this key secure and never share it

#### Serper API Key (for web search)
1. Go to [Serper.dev](https://serper.dev)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Copy the key and paste it in your `.env` file

### Step 5: Run MarketMinds

#### Option 1: Web Interface (Recommended for beginners)
```bash
# Make sure your virtual environment is activated
streamlit run app.py
```

Then:
1. Open your web browser
2. Navigate to `http://localhost:8501`
3. You'll see the MarketMinds interface
4. Configure your product details in the sidebar
5. Click "Start Comprehensive Analysis"
6. Wait for the AI crew to complete their research
7. Download the generated reports

#### Option 2: Command Line (For advanced users)
```bash
# Make sure your virtual environment is activated
python main.py
```

This will:
- Use the default product settings from your `.env` file
- Run the analysis automatically
- Generate reports in the project directory
- Show progress in the terminal

### Step 6: View Results

After the analysis completes, you'll find these files in your project directory:
- `final_market_analysis_report.md` - Complete market analysis
- `competitor_analysis.md` - Detailed competitor research
- `customer_analysis.md` - User persona analysis
- `risk_analysis.md` - Risk assessment
- `research_plan.md` - Initial research framework

## 🔧 Troubleshooting

### Common Issues

#### "Module not found" errors
```bash
# Make sure your virtual environment is activated
# Then reinstall dependencies
pip install -r requirements.txt
```

#### API key errors
- Double-check your API keys in the `.env` file
- Ensure there are no extra spaces or quotes around the keys
- Verify your API keys are valid and have sufficient credits

#### Streamlit not starting
```bash
# Try installing streamlit separately
pip install streamlit
streamlit run app.py
```

#### Permission errors (Windows)
- Run Command Prompt as Administrator
- Or use PowerShell instead of Command Prompt

### Getting Help

If you encounter issues:
1. Check that all prerequisites are installed
2. Verify your API keys are correct
3. Ensure your virtual environment is activated
4. Check the console output for specific error messages

## 📊 What You Get

After running an analysis, you'll receive comprehensive reports including:

- **Competitor Analysis**: Detailed scoring of competitors with market share distribution
- **Customer Personas**: Rich, data-driven user profiles
- **Risk Assessment**: Critical evaluation of market opportunities and threats
- **Strategic Recommendations**: Actionable insights for your business
- **Evidence Documentation**: All sources and data points with real URLs


### Agent Collaboration

Each agent has a unique personality and expertise, working together like a dream team of consultants:

- **Strategy Consultant**: The quarterback who frames the research
- **Competitor Analyst**: The detective who digs deep into the competition
- **Customer Persona Analyst**: The empath who understands user needs
- **Devil's Advocate**: The skeptic who keeps everyone honest
- **Lead Synthesizer**: The strategist who turns insights into action

## 💻 Code Deep Dive

### Core Components

#### 1. **agents.py** - The AI Crew
This file defines each specialized AI agent with unique personalities and capabilities:

```python
# Example: Strategy Consultant Agent
def strategy_consultant(self):
    return Agent(
        role='Strategy Consultant',
        goal="Analyze initial product and market information to formulate probing questions",
        backstory="A seasoned consultant from McKinsey, you excel at framing complex business problems",
        tools=[],  # Uses LLM reasoning capabilities
        verbose=True
    )
```

**Key Features:**
- Each agent has a specific role, goal, and backstory
- Agents use different tools based on their expertise
- Personality-driven responses for more human-like analysis

#### 2. **tasks.py** - Research Tasks
Defines the specific tasks each agent performs:

```python
# Example: Competitor Analysis Task
def competitor_analysis_task(self, agent):
    return Task(
        description="Conduct exhaustive analysis of competitive landscape...",
        expected_output="Detailed competitor analysis with scoring rubrics...",
        agent=agent,
        output_file='competitor_analysis.md'
    )
```

**Key Features:**
- Structured task definitions with clear outputs
- Evidence-based scoring systems
- Real URL documentation requirements

#### 3. **app.py** - Web Interface
Streamlit-based UI for easy interaction:

```python
# Main interface setup
st.title("🤖 Strategic Market Research AI Crew")
st.write("This AI crew conducts comprehensive market analysis...")

# Sidebar configuration
with st.sidebar:
    product_name_input = st.text_input("Product/Service Name")
    industry_input = st.text_input("Target Industry")
    # ... more configuration options
```

**Key Features:**
- User-friendly web interface
- Real-time progress tracking
- Downloadable reports
- Debug mode for developers

#### 4. **main.py** - Command Line Interface
Entry point for command-line usage:

```python
# Main execution flow
def main():
    # Initialize agents
    agents = MarketResearchAgents()
    
    # Create tasks
    tasks = MarketResearchTasks()
    
    # Assemble crew
    crew = Crew(
        agents=[...],
        tasks=[...],
        verbose=True
    )
    
    # Execute research
    result = crew.kickoff()
```

### Multi-Agent Workflow

1. **Initialization**: Agents are created with specific roles and tools
2. **Task Assignment**: Each agent receives specialized tasks
3. **Parallel Execution**: Agents work simultaneously on their tasks
4. **Information Sharing**: Agents can read each other's outputs
5. **Critical Review**: Devil's Advocate reviews all findings
6. **Final Synthesis**: Lead Synthesizer combines everything

### Key Technologies Used

- **CrewAI**: Multi-agent framework for AI collaboration
- **OpenAI GPT**: Language model for agent reasoning
- **Streamlit**: Web interface framework
- **Serper API**: Web search capabilities
- **Firecrawl**: Website scraping for competitor research

### Custom Tools

The system includes custom tools for enhanced research:

```python
# Web Search Tool
class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web for current information"
    
    def _run(self, query: str) -> str:
        # Implementation for web search
        pass
```

### Environment Configuration

The system uses environment variables for configuration:

```bash
# Required API Keys
OPENAI_API_KEY=your_openai_key
SERPER_API_KEY=your_serper_key

# Optional Product Settings
PRODUCT_NAME=Your Product
PRODUCT_DESCRIPTION=Your description
INDUSTRY=Your industry
GEOGRAPHY=Your geography
```

### Report Generation

The system generates multiple markdown reports:

- **Comprehensive Analysis**: Complete market research document
- **Competitor Analysis**: Detailed competitive intelligence
- **Customer Analysis**: User persona research
- **Risk Assessment**: Critical evaluation and risks
- **Research Plan**: Initial framework and questions

Each report includes:
- Evidence-based scoring
- Real URLs and sources
- Actionable recommendations
- Detailed rationale for all conclusions



## Connect

- **LinkedIn**: https://www.linkedin.com/in/anamikabharali/ 


---

*Built with passion and enthusiasm for the future of AI-powered market research! *


---

**Follow [Humanitarians AI](https://humanitarians.ai) for more sophisticated versions and ambitious AI projects.**
