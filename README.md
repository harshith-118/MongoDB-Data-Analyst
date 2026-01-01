# MongoDB Data Analyst

A LangGraph-powered natural language interface for querying MongoDB databases with a beautiful Streamlit web UI. Ask questions in plain English and get accurate, validated answers from your data.

![MongoDB Data Analyst](https://img.shields.io/badge/MongoDB-Data%20Analyst-10b981?style=for-the-badge&logo=mongodb)

## ✨ Features

- **🎨 Beautiful Web UI**: Modern, dark-themed Streamlit interface
- **💬 Natural Language Queries**: Ask questions about your data in plain English
- **🤖 Automatic Query Generation**: Uses OpenAI GPT to convert questions into MongoDB queries
- **🔍 Hallucination Detection**: Automatically detects and retries hallucinations in queries and summaries (up to 3 retries)
- **📝 Intelligent Summarization**: Get natural language answers from query results
- **📊 Schema-Aware**: Automatically discovers your database schema
- **📈 Rich Results Display**: View results as tables, JSON, or download as CSV
- **🔒 Input Validation**: Validates and sanitizes user input for security
- **💾 Chat History**: Keep track of your queries and results
- **🎬 Sample Database Setup**: Includes script to create a cinema database for testing

## 🏗️ Architecture

The system uses a sophisticated workflow with built-in hallucination detection at multiple stages:

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────────────┐
│  __start__  │ ──▶ │  Input Validator │ ──▶ │ Exploration Node │ ──▶ │ Query Hallucination Node │
└─────────────┘     └──────────────────┘     └──────────────────┘     └──────────────────────────┘
                           │                          │                              │
                           ▼                          ▼                              │
                    Validates &              Generates MongoDB              Detects hallucinations
                    cleans input              query via LLM                  (retry if detected)
                                                                                    │
                                                                                    ▼
┌─────────────┐     ┌──────────────────┐     ┌──────────────────────────┐     ┌───────────┐
│  __end__    │ ◀─── │Summary Halluc. Node│ ◀─── │Summarization Node        │ ◀─── │MongoDB Node│
└─────────────┘     └──────────────────┘     └──────────────────────────┘     └───────────┘
                           │                              │                              │
                           ▼                              ▼                              ▼
                    Detects hallucinations      Generates natural          Executes query
                    (retry if detected)        language summary           and returns results
```

## 🔍 Hallucination Detection System

### Query Hallucination Detection

The system validates every generated MongoDB query before execution:

- ✅ **Schema Validation**: Checks if collections and fields exist in the database
- ✅ **Syntax Validation**: Verifies MongoDB query syntax is correct
- ✅ **Intent Matching**: Ensures the query matches the user's question intent
- ✅ **Automatic Retry**: Retries query generation up to 3 times if hallucinations detected

**What it detects:**
- References to non-existent collections
- Invalid field names
- Incorrect MongoDB operators
- Queries that don't match the user's intent

### Summary Hallucination Detection

The system validates every summary against actual query results:

- ✅ **Factual Accuracy**: Verifies all claims are supported by the data
- ✅ **Number Verification**: Ensures statistics and counts match the results
- ✅ **Name Verification**: Checks that names and identifiers are correct
- ✅ **Automatic Retry**: Retries summary generation up to 3 times if hallucinations detected

**What it detects:**
- Claims not supported by the data
- Incorrect numbers or statistics
- Made-up names or identifiers
- Information not present in query results

**Recent Improvements:**
- Enhanced validation prompts to reduce false positives
- Better distinction between factual errors and wording differences
- More accurate detection of actual hallucinations vs. correct statements

### Retry Logic

- **Maximum Retries**: 3 attempts for both queries and summaries
- **Smart Tracking**: Retry counters prevent infinite loops
- **Graceful Degradation**: After max retries, accepts the result to ensure workflow completion
- **LLM-Powered Validation**: Uses OpenAI GPT for intelligent fact-checking

## 📦 Installation

1. **Clone or download this project**

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Create a `.env` file** in the project root with your configuration:

```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=your_database_name

# OpenAI API Configuration  
LLM_API_KEY=your_openai_api_key_here

# Optional: Logging Configuration
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=logs/mongodb_analyst.log  # Optional: log to file

# Optional: Rate Limiting Configuration
RATE_LIMIT_CALLS=60  # Max API calls per period
RATE_LIMIT_PERIOD=60  # Time period in seconds
```

> **Note**: This project uses OpenAI's API directly. You'll need an OpenAI API key. Get one at [platform.openai.com](https://platform.openai.com/api-keys)

> ⚠️ **Important**: Never commit your `.env` file to version control! It's already in `.gitignore`.

## 🚀 Usage

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

## 🎯 Web UI Features

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

## 💡 Example Questions

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

## 📁 Project Structure

```
├── app.py                    # Streamlit web application
├── main.py                   # CLI entry point
├── setup.py                  # Package setup script
├── setup_cinema_db.py        # Script to create sample cinema database
├── requirements.txt          # Python dependencies
├── pytest.ini                # Pytest configuration
├── .env.example              # Environment variables template
├── src/                      # Source code directory
│   └── mongodb_analyst/      # Main package
│       ├── __init__.py       # Package exports
│       ├── graph/            # Graph workflow module
│       │   ├── __init__.py
│       │   ├── graph.py      # Main workflow definition
│       │   ├── state.py      # Graph state definition
│       │   ├── nodes.py      # All graph node functions
│       │   └── utils.py      # Graph utility functions
│       ├── llm/              # LLM utilities module
│       │   ├── __init__.py
│       │   ├── sync.py       # Synchronous LLM calls
│       │   └── async_utils.py # Asynchronous LLM calls
│       ├── prompts/          # Prompt templates module
│       │   └── __init__.py   # All prompt templates
│       ├── mongodb/          # MongoDB utilities module
│       │   ├── __init__.py
│       │   └── connection.py # MongoDB connection and queries
│       ├── monitoring/       # Monitoring module
│       │   ├── __init__.py
│       │   └── metrics.py    # Metrics and health checks
│       └── config/           # Configuration module
│           ├── __init__.py
│           ├── settings.py   # Environment configuration
│           ├── logger.py     # Logging configuration
│           └── rate_limiter.py # Rate limiting
├── tests/                    # Test directory
│   ├── __init__.py
│   ├── test_graph_utils.py
│   └── test_monitoring.py
├── logs/                     # Log files directory
└── README.md                 # This file
```

## 🔄 How It Works

The complete workflow with hallucination detection:

1. **User asks a question** - Natural language input via web UI or CLI
2. **Input Validator** - Validates the question and retrieves database schema
3. **Exploration Node** - Uses OpenAI GPT to generate a MongoDB query
4. **Query Hallucination Detection** - Validates the generated query:
   - Checks for non-existent collections
   - Verifies field names exist in collections
   - Validates MongoDB syntax
   - Ensures query matches user intent
   - **Retries up to 3 times** if hallucinations detected
5. **MongoDB Node** - Executes the validated query and retrieves results
6. **Summarization Node** - Uses OpenAI GPT to generate a natural language answer
7. **Summary Hallucination Detection** - Validates the summary:
   - Verifies factual accuracy
   - Checks for unsupported claims
   - Ensures correct numbers and names
   - **Retries up to 3 times** if hallucinations detected
8. **User gets the answer** - Natural language summary displayed prominently, with detailed results available in expandable sections

## ⚙️ Configuration

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

## 🛠️ Tech Stack

- **LangGraph** - Workflow orchestration with conditional routing
- **Streamlit** - Web UI framework
- **PyMongo** - MongoDB driver
- **Pandas** - Data manipulation
- **OpenAI API** - Natural language processing, query generation, summarization, and hallucination detection
- **Pytest** - Testing framework
- **Python Logging** - Comprehensive logging system
- **Rate Limiting** - API call throttling and management

## 🧪 Testing

The project includes a comprehensive test suite using `pytest`. Run tests to verify everything is working correctly:

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_graph_utils.py
pytest tests/test_monitoring.py
```

### Test Coverage

The test suite includes:
- **Graph Utilities Tests** (`test_graph_utils.py`): Tests for formatting, cleaning, and utility functions
- **Monitoring Tests** (`test_monitoring.py`): Tests for metrics collection and health checks

Tests can be run without a live MongoDB connection as they use mocked dependencies.

## 💻 Developer Guide

### Using Logging

The project includes a centralized logging system. Import and use the logger throughout your code:

```python
from src.mongodb_analyst.config.logger import logger

logger.info("This is an info message")
logger.error("This is an error message", exc_info=True)
logger.debug("This is a debug message")
logger.warning("This is a warning message")
```

**Log Configuration:**
- Logs are written to `logs/mongodb_analyst.log` by default
- Rotating file handler (10MB, 5 backups)
- Configurable log level via `LOG_LEVEL` environment variable
- Console and file handlers for comprehensive logging

### Using Metrics and Health Checks

Monitor system performance and health:

```python
from src.mongodb_analyst.monitoring import metrics_collector, HealthChecker

# Get current metrics
metrics = metrics_collector.get_metrics()
print(f"Total queries: {metrics['total_queries']}")
print(f"Success rate: {metrics['success_rate']*100:.1f}%")
print(f"API calls: {metrics['api_calls']}")

# Check system health
health = HealthChecker.get_health_status()
if health["status"] == "healthy":
    print("All systems operational")
else:
    print(f"MongoDB: {health['mongodb']['status']}")
    print(f"OpenAI: {health['openai']['status']}")
```

**Available Metrics:**
- Total queries, successful/failed queries
- Hallucination detections and retries
- API call counts
- Average query execution time
- Success/failure rates

### Using Rate Limiting

Rate limiting is automatically applied to API calls, but you can also use it manually:

```python
from src.mongodb_analyst.config.rate_limiter import api_rate_limiter

# Wait if needed before making API call
api_rate_limiter.wait_if_needed()
# ... make your API call ...
```

**Rate Limit Configuration:**
- Default: 60 calls per 60 seconds
- Configurable via `RATE_LIMIT_CALLS` and `RATE_LIMIT_PERIOD` in `.env`
- Prevents API throttling and rate limit errors

### Package Installation

Install the package in development mode:

```bash
pip install -e .
```

This allows you to import from `mongodb_analyst` directly:

```python
from mongodb_analyst.graph import ask_question
from mongodb_analyst.mongodb import mongo_connection
from mongodb_analyst.config import LLM_API_KEY
```

## 📚 Key Features Explained

### 🤖 Query Generation
The system uses OpenAI GPT to understand your natural language question and automatically generates an appropriate MongoDB query. It considers your database schema to create accurate queries.

### 🔍 Hallucination Detection
**This is a key feature that sets this system apart!** The system includes two-stage hallucination detection:

1. **Query Validation**: Before executing any query, the system validates it against your actual database schema to ensure it references real collections and fields.

2. **Summary Validation**: After generating a summary, the system fact-checks it against the actual query results to ensure all claims are accurate.

Both validation stages use OpenAI GPT for intelligent fact-checking and automatically retry up to 3 times if issues are detected.

**Recent Improvements:**
- Enhanced validation prompts to reduce false positives
- Better distinction between factual errors and wording differences
- More accurate detection focusing on actual data contradictions
- Improved handling of correct statements that may be worded differently

### 📝 Result Summarization
After executing the query, the system uses OpenAI GPT to analyze the results and provide a natural language answer. The summary is then validated against the actual data to ensure accuracy.

### 🎬 Sample Database
The included `setup_cinema_db.py` script creates a comprehensive cinema database with realistic relationships between movies, theaters, showtimes, customers, tickets, reviews, and staff. Perfect for testing and demonstrations.

## 🐛 Troubleshooting

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

**Hallucination Detection Warnings**
- If queries are being retried multiple times, check your database schema
- Ensure collection and field names in your database match common naming conventions
- The system will accept results after 3 retry attempts to prevent infinite loops
- Check the generated query in the expandable section to see what was ultimately used
- If summaries are being retried, verify that your query results contain the expected data
- **False Positives**: The system has been improved to reduce false positives. If you see hallucination warnings for correct summaries, check the logs for details - the system now better distinguishes between factual errors and correct statements with different wording

## 📝 Recent Updates

### Latest Improvements (v2.0)

#### 🏗️ Architecture & Code Quality
- ✅ **Modular Architecture**: Reorganized code into `src/` with logical module structure
  - `src/mongodb_analyst/graph/` - All graph-related code (workflow, nodes, state, utils)
  - `src/mongodb_analyst/llm/` - LLM utilities (synchronous and asynchronous)
  - `src/mongodb_analyst/prompts/` - All prompt templates
  - `src/mongodb_analyst/mongodb/` - MongoDB connection and query utilities
  - `src/mongodb_analyst/monitoring/` - Metrics collection and health checks
  - `src/mongodb_analyst/config/` - Configuration, logging, and rate limiting
- ✅ **Package Structure**: Proper Python package structure with `setup.py` for easy installation
- ✅ **Better Code Organization**: Reduced large files (graph.py from 963 lines to ~150 lines)
- ✅ **Improved Maintainability**: Clear module boundaries and separation of concerns

#### 🔍 Quality & Reliability
- ✅ **Improved Hallucination Detection**: Enhanced validation prompts to reduce false positives
- ✅ **Comprehensive Logging System**: 
  - Centralized logging with file and console handlers
  - Rotating file handler (10MB, 5 backups)
  - Configurable log levels via environment variables
- ✅ **Unit Tests**: Comprehensive test suite with pytest
  - Tests for graph utilities
  - Tests for monitoring and metrics
  - Can run without live MongoDB connection (mocked)

#### ⚡ Performance & Operations
- ✅ **Async Operations**: Async LLM calls for better performance with batch processing support
- ✅ **Rate Limiting**: 
  - Token bucket rate limiter
  - Configurable limits via environment variables
  - Automatic waiting when limits are reached
  - Prevents API throttling
- ✅ **Monitoring & Metrics**: 
  - Real-time metrics tracking (queries, API calls, performance)
  - Health checks for MongoDB and OpenAI connections
  - System health monitoring in UI sidebar

#### 📦 Developer Experience
- ✅ **Environment Template**: `.env.example` file for easy setup
- ✅ **Comprehensive Documentation**: Updated README with all features and usage examples
- ✅ **Easy to Extend**: Clear module structure makes adding features straightforward

### Hallucination Detection System
- ✅ Added query hallucination detection node
- ✅ Added summary hallucination detection node
- ✅ Automatic retry logic (up to 3 attempts)
- ✅ Schema-based query validation
- ✅ Fact-checking for summaries against actual results
- ✅ **Improved validation prompts to reduce false positives**
- ✅ Improved accuracy and reliability

### Previous Updates
- ✅ Direct OpenAI API integration (no URL dependency)
- ✅ Intelligent result summarization
- ✅ Enhanced UI with prominent answer display
- ✅ Cinema database setup script
- ✅ Improved query parsing and error handling

## 📊 Impact & Benefits

### Code Quality
- ✅ **Better Organization**: Modular structure with clear separation of concerns
- ✅ **Improved Maintainability**: Smaller, focused modules are easier to understand and modify
- ✅ **Easier Testing**: Individual components can be tested in isolation
- ✅ **Better Error Tracking**: Comprehensive logging system for debugging

### Performance
- ✅ **Async Operations**: Better concurrency for multiple concurrent requests
- ✅ **Rate Limiting**: Prevents API throttling and ensures reliable operation
- ✅ **Metrics Tracking**: Monitor performance and identify bottlenecks

### Reliability
- ✅ **Health Checks**: Proactive monitoring of system components
- ✅ **Comprehensive Logging**: Detailed logs for debugging and troubleshooting
- ✅ **Unit Tests**: Regression prevention and code quality assurance

### Developer Experience
- ✅ **Clear Module Structure**: Easy to navigate and understand the codebase
- ✅ **Comprehensive Documentation**: Well-documented code and usage examples
- ✅ **Easy to Extend**: Modular design makes adding new features straightforward
- ✅ **Package Installation**: Can be installed as a proper Python package

## 📄 License

This project is open source and available for use and modification.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

**Made with ❤️ using LangGraph, Streamlit, and OpenAI**
