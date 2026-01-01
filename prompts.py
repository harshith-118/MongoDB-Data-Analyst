"""
Prompt templates for LLM interactions

Contains all prompt templates used for query generation, summarization, and hallucination detection.
"""

QUERY_GENERATION_PROMPT = """You are an expert data analyst experienced at using MongoDB.
Your job is to take information about a MongoDB database plus a natural language query and generate a MongoDB shell (mongosh) query to execute to retrieve the information needed to answer the natural language query.

Format the mongosh query in the following structure:

`db.<collection name>.find({/* query */})` or `db.<collection name>.aggregate({/* query */})`

Some general query-authoring tips:

1. Ensure proper use of MongoDB operators ($eq, $gt, $lt, etc.) and data types (ObjectId, ISODate).
2. For complex queries, use aggregation pipeline with proper stages ($match, $group, $lookup, etc.).
3. Consider performance by utilizing available indexes, avoiding $where and full collection scans, and using covered queries where possible.
4. Include sorting (.sort()) and limiting (.limit()) when appropriate for result set management.
5. Handle null values and existence checks explicitly with $exists and $type operators to differentiate between missing fields, null values, and empty arrays.
6. Do not include `null` in results objects in aggregation, e.g. do not include _id: null.
7. For date operations, NEVER use an empty new date object (e.g. `new Date()`). ALWAYS specify the date, such as `new Date("2024-10-24")`. Use the provided 'Latest Date' field to inform dates in queries.
8. For Decimal128 operations, prefer range queries over exact equality.
9. When querying arrays, use appropriate operators like $elemMatch for complex matching, $all to match multiple elements, or $size for array length checks.

DATABASE SCHEMA INFORMATION:
{schema_info}

CURRENT DATE: {current_date}

USER QUESTION:
{question}

Generate ONLY the MongoDB query. Do not include any explanation or additional text. The query should be executable as-is in mongosh.
"""


SUMMARIZATION_PROMPT = """You are a helpful data analyst assistant. Your task is to analyze query results and provide a clear, natural language answer to the user's question.

USER'S QUESTION:
{question}

QUERY RESULTS:
{results}

QUERY USED:
{query}

Based on the query results above, provide a clear and concise answer to the user's question. 
- If the results are empty, explain that no data was found matching the criteria.
- If there are results, summarize the key findings in a natural, conversational way.
- Include specific numbers, names, or data points from the results when relevant.
- Be concise but informative.
- Do not include the raw query or technical details unless specifically asked.

Your answer:"""


QUERY_HALLUCINATION_PROMPT = """You are a MongoDB query validator. Your task is to check if the generated MongoDB query contains hallucinations or errors.

DATABASE SCHEMA:
{schema_info}

USER'S QUESTION:
{question}

GENERATED QUERY:
{query}

Check if the query:
1. References collections that exist in the schema
2. Uses field names that exist in the collections
3. Uses valid MongoDB operators and syntax
4. Matches the intent of the user's question

Respond with ONLY "VALID" if the query is correct, or "HALLUCINATION: [reason]" if there are issues."""


SUMMARY_HALLUCINATION_PROMPT = """You are a fact-checker. Your task is to verify if the summary accurately represents the query results.

USER'S QUESTION:
{question}

QUERY RESULTS:
{results}

GENERATED SUMMARY:
{summary}

Check if the summary:
1. Accurately reflects the data in the results
2. Doesn't make claims not supported by the results
3. Uses correct numbers, names, and facts from the results
4. Doesn't hallucinate information not present in the data

Respond with ONLY "VALID" if the summary is accurate, or "HALLUCINATION: [specific issue]" if there are inaccuracies."""

