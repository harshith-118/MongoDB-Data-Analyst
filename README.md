# MongoDB Data Analyst

A LangGraph-powered natural language interface for querying MongoDB databases with a beautiful Streamlit web UI. Ask questions in plain English and get answers from your data.

![MongoDB Data Analyst](https://img.shields.io/badge/MongoDB-Data%20Analyst-10b981?style=for-the-badge&logo=mongodb)

## Features

- **🎨 Beautiful Web UI**: Modern, dark-themed Streamlit interface
- **💬 Natural Language Queries**: Ask questions about your data in plain English
- **🤖 Automatic Query Generation**: Uses OpenAI GPT to convert questions into MongoDB queries
- **📝 Intelligent Summarization**: Get natural language answers from query results
- **📊 Schema-Aware**: Automatically discovers your database schema
- **📈 Rich Results Display**: View results as tables, JSON, or download as CSV
- **🔒 Input Validation**: Validates and sanitizes user input for security
- **💾 Chat History**: Keep track of your queries and results
- **🎬 Sample Database Setup**: Includes script to create a cinema database for testing

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌─────────────┐     ┌──────────────────┐     ┌───────────┐
│  __start__  │ ──▶ │  Input Validator │ ──▶ │ Exploration Node │ ──▶ │ MongoDB Node│ ──▶ │Summarization Node│ ──▶ │  __end__  │
└─────────────┘     └──────────────────┘     └──────────────────┘     └─────────────┘     └──────────────────┘     └───────────┘
                           │                          │                      │                        │
                           ▼                          ▼                      ▼                        ▼
                    Validates &              Generates MongoDB         Executes query      Generates natural
                    cleans input              query via LLM            and returns results  language summary
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

# OpenAI API Configuration  
LLM_API_KEY=your_openai_api_key_here
```

> **Note**: This project uses OpenAI's API directly. You'll need an OpenAI API key. Get one at [platform.openai.com](https://platform.openai.com/api-keys)

> ⚠️ **Important**: Never commit your `.env` file to version control! It's already in `.gitignore`.

## Usage

### 🎬 Setup Sample Database (Optional)

To test the application with sample data, you can create a cinema database:

```bash
python setup_cinema_db.py
```

This will create a `cinema_db` database with collections for movies, theaters, showtimes, customers, tickets, reviews, and staff. Update your `.env` file to use this database:

```env
MONGODB_DATABASE=cinema_db
```

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
- **Natural Language Answers**: Get summarized, conversational answers to your questions
- **Results Display**: View generated queries and results in collapsible sections
- **Data Table**: Interactive table with sorting and filtering (inside expandable section)
- **CSV Download**: Export results for further analysis
- **Chat History**: Review previous queries and answers

## Example Questions

**General Database Queries:**
- "How many documents are in each collection?"
- "Show me all orders from last month"
- "What is the average price of products?"
- "Find the top 10 customers by total purchase amount"
- "List all products where quantity is less than 10"
- "Count users grouped by country"

**Cinema Database Examples** (if using the sample database):
- "How many movies are in the database?"
- "Show me all movies directed by Christopher Nolan"
- "What are the average ratings for each movie?"
- "List all theaters in New York"
- "How many tickets were sold last week?"
- "What movies are showing today?"

## Project Structure

```
├── app.py                # Streamlit web application
├── main.py               # CLI entry point
├── graph.py              # LangGraph workflow definition
├── mongodb_utils.py      # MongoDB connection and query utilities
├── config.py             # Configuration settings
├── setup_cinema_db.py    # Script to create sample cinema database
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## How It Works

1. **User asks a question** - Natural language input via web UI or CLI
2. **Input Validator** - Validates the question and retrieves database schema
3. **Exploration Node** - Uses OpenAI GPT to generate a MongoDB query
4. **MongoDB Node** - Executes the query and retrieves results
5. **Summarization Node** - Uses OpenAI GPT to generate a natural language answer from the results
6. **User gets the answer** - Natural language summary displayed prominently, with detailed results available in expandable sections

## Configuration

All configuration is done via environment variables in a `.env` file:

| Variable | Description | Example |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGODB_DATABASE` | Database name to query | `my_database` |
| `LLM_API_KEY` | OpenAI API key | `sk-xxx...` |

> **Note**: This project uses OpenAI's API directly. You no longer need to provide a custom API URL.

### Example `.env` file

```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=sample_database

# OpenAI API Configuration
LLM_API_KEY=sk-your_openai_api_key_here
```

> 💡 **Tip**: Copy the example above and save it as `.env` in your project root.

## Tech Stack

- **LangGraph** - Workflow orchestration
- **Streamlit** - Web UI framework
- **PyMongo** - MongoDB driver
- **Pandas** - Data manipulation
- **OpenAI API** - Natural language to query conversion and result summarization

## Key Features Explained

### 🤖 Query Generation
The system uses OpenAI GPT to understand your natural language question and automatically generates an appropriate MongoDB query. It considers your database schema to create accurate queries.

### 📝 Result Summarization
After executing the query, the system uses OpenAI GPT again to analyze the results and provide a natural language answer. This makes the data more accessible and easier to understand.

### 🎬 Sample Database
The included `setup_cinema_db.py` script creates a comprehensive cinema database with realistic relationships between movies, theaters, showtimes, customers, tickets, reviews, and staff. Perfect for testing and demonstrations.

## Troubleshooting

### Common Issues

**"Could not parse collection name from query"**
- The query parser has been improved to handle various query formats
- If you encounter this, check the generated query in the expandable section
- The error message will show the first 200 characters of the query for debugging

**OpenAI API Errors**
- Ensure your API key is valid and has sufficient credits
- Check that you're using the correct API key format (starts with `sk-`)
- Verify your OpenAI account has access to the API

**MongoDB Connection Issues**
- Verify your MongoDB instance is running
- Check that the connection string in `.env` is correct
- Ensure the database name exists (or use the setup script to create the sample database)
