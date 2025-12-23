# MongoDB Data Analyst

A LangGraph-powered natural language interface for querying MongoDB databases with a beautiful Streamlit web UI. Ask questions in plain English and get answers from your data.

![MongoDB Data Analyst](https://img.shields.io/badge/MongoDB-Data%20Analyst-10b981?style=for-the-badge&logo=mongodb)

## Features

- **🎨 Beautiful Web UI**: Modern, dark-themed Streamlit interface
- **💬 Natural Language Queries**: Ask questions about your data in plain English
- **🤖 Automatic Query Generation**: Uses GPT to convert questions into MongoDB queries
- **📊 Schema-Aware**: Automatically discovers your database schema
- **📈 Rich Results Display**: View results as tables, JSON, or download as CSV
- **🔒 Input Validation**: Validates and sanitizes user input for security
- **💾 Chat History**: Keep track of your queries and results

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌─────────────┐     ┌───────────┐
│  __start__  │ ──▶ │  Input Validator │ ──▶ │ Exploration Node │ ──▶ │ MongoDB Node│ ──▶ │  __end__  │
└─────────────┘     └──────────────────┘     └──────────────────┘     └─────────────┘     └───────────┘
                           │                          │                      │
                           ▼                          ▼                      ▼
                    Validates &              Generates MongoDB         Executes query
                    cleans input              query via LLM            and returns results
```

## Installation

1. Clone or download this project

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your configuration:

```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=your_database_name

# LLM API Configuration  
LLM_API_URL=https://your-api-endpoint.com/api/v1/chat
LLM_API_KEY=your_api_key_here
```

> ⚠️ **Important**: Never commit your `.env` file to version control! It's already in `.gitignore`.

## Usage

### 🌐 Web UI (Recommended)

Start the Streamlit web application:

```bash
streamlit run app.py
```

Or use the main script:

```bash
python main.py --web
```

Then open http://localhost:8501 in your browser.

### 💻 Command Line

**Interactive Mode:**
```bash
python main.py
```

**Single Query:**
```bash
python main.py "How many documents are in the users collection?"
```

**Help:**
```bash
python main.py --help
```

## Web UI Features

### Sidebar
- **Connection Status**: Shows MongoDB connection state
- **Database Schema**: Browse collections and fields
- **Quick Actions**: Refresh schema, clear history
- **Example Questions**: Get started with sample queries

### Main Area
- **Query Input**: Type questions in natural language
- **Results Display**: View generated queries and results
- **Data Table**: Interactive table with sorting and filtering
- **CSV Download**: Export results for further analysis
- **Chat History**: Review previous queries

## Example Questions

- "How many documents are in each collection?"
- "Show me all orders from last month"
- "What is the average price of products?"
- "Find the top 10 customers by total purchase amount"
- "List all products where quantity is less than 10"
- "Count users grouped by country"

## Project Structure

```
├── app.py            # Streamlit web application
├── main.py           # CLI entry point
├── graph.py          # LangGraph workflow definition
├── mongodb_utils.py  # MongoDB connection and query utilities
├── config.py         # Configuration settings
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

## How It Works

1. **User asks a question** - Natural language input via web UI or CLI
2. **Input Validator** - Validates the question and retrieves database schema
3. **Exploration Node** - Uses LLM to generate a MongoDB query
4. **MongoDB Node** - Executes the query and formats results
5. **User gets the answer** - Results displayed in the web UI or terminal

## Configuration

All configuration is done via environment variables in a `.env` file:

| Variable | Description | Example |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGODB_DATABASE` | Database name to query | `my_database` |
| `LLM_API_URL` | LLM API endpoint | `https://api.example.com/chat` |
| `LLM_API_KEY` | API authentication key | `sk-xxx...` |

### Example `.env` file

```env
# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=sample_database

# LLM API
LLM_API_URL=https://aigateway-api.example.com/api/v1/chat
LLM_API_KEY=your_secret_api_key
```

> 💡 **Tip**: Copy the example above and save it as `.env` in your project root.

## Tech Stack

- **LangGraph** - Workflow orchestration
- **Streamlit** - Web UI framework
- **PyMongo** - MongoDB driver
- **Pandas** - Data manipulation
- **GPT API** - Natural language to query conversion
