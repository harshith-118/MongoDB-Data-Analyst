"""
MongoDB Connection and Query Execution Utilities
"""
import re
from typing import Any, Dict, List, Optional, Tuple
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import PyMongoError
from bson import ObjectId
from datetime import datetime

from config import MONGODB_URI, MONGODB_DATABASE


class MongoDBConnection:
    """Manages MongoDB connection and query execution"""
    
    _instance: Optional['MongoDBConnection'] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def connect(self, uri: str = MONGODB_URI, database: str = MONGODB_DATABASE) -> Database:
        """Establish connection to MongoDB"""
        if self._client is None:
            self._client = MongoClient(uri)
            self._db = self._client[database]
        return self._db
    
    def get_database(self) -> Database:
        """Get the current database connection"""
        if self._db is None:
            return self.connect()
        return self._db
    
    def close(self):
        """Close the MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
    
    def get_schema_info(self) -> Dict[str, Any]:
        """
        Get schema information for all collections in the database.
        This helps the LLM understand the database structure.
        """
        db = self.get_database()
        schema_info = {
            "database_name": db.name,
            "collections": []
        }
        
        for collection_name in db.list_collection_names():
            collection = db[collection_name]
            
            # Get sample document to infer schema
            sample_doc = collection.find_one()
            
            # Get document count
            doc_count = collection.estimated_document_count()
            
            # Get indexes
            indexes = list(collection.list_indexes())
            
            collection_info = {
                "name": collection_name,
                "document_count": doc_count,
                "sample_fields": self._extract_fields(sample_doc) if sample_doc else [],
                "indexes": [idx.get("key") for idx in indexes]
            }
            
            schema_info["collections"].append(collection_info)
        
        return schema_info
    
    def _extract_fields(self, doc: Dict, prefix: str = "") -> List[Dict[str, str]]:
        """Extract field names and types from a document"""
        fields = []
        for key, value in doc.items():
            field_path = f"{prefix}.{key}" if prefix else key
            field_type = type(value).__name__
            
            if isinstance(value, dict):
                fields.append({"field": field_path, "type": "object"})
                fields.extend(self._extract_fields(value, field_path))
            elif isinstance(value, list):
                fields.append({"field": field_path, "type": "array"})
                if value and isinstance(value[0], dict):
                    fields.extend(self._extract_fields(value[0], f"{field_path}[]"))
            else:
                fields.append({"field": field_path, "type": field_type})
        
        return fields
    
    def execute_query(self, query_string: str) -> Tuple[bool, Any]:
        """
        Execute a MongoDB query string and return results.
        
        Args:
            query_string: A MongoDB shell query string (e.g., db.collection.find({...}))
            
        Returns:
            Tuple of (success: bool, result: data or error message)
        """
        db = self.get_database()
        
        try:
            # Parse the query string to extract collection, method, and parameters
            collection_name, method, params = self._parse_query(query_string)
            
            if not collection_name:
                return False, "Could not parse collection name from query"
            
            collection = db[collection_name]
            
            # Execute based on method type
            if method == "find":
                result = self._execute_find(collection, params)
            elif method == "aggregate":
                result = self._execute_aggregate(collection, params)
            elif method == "count" or method == "countDocuments":
                result = self._execute_count(collection, params)
            else:
                return False, f"Unsupported method: {method}"
            
            return True, result
            
        except PyMongoError as e:
            return False, f"MongoDB Error: {str(e)}"
        except Exception as e:
            return False, f"Execution Error: {str(e)}"
    
    def _parse_query(self, query_string: str) -> Tuple[Optional[str], Optional[str], str]:
        """
        Parse a MongoDB shell query string to extract components.
        
        Returns:
            Tuple of (collection_name, method, parameters_string)
        """
        # Clean up the query string
        query_string = query_string.strip()
        
        # Pattern to match: db.collection.method(params)
        pattern = r'db\.([a-zA-Z_][a-zA-Z0-9_]*)\.(\w+)\s*\((.*)\)\s*(?:\.sort\((.*?)\))?\s*(?:\.limit\((\d+)\))?'
        
        # First try a simpler pattern for basic queries
        simple_pattern = r'db\.([a-zA-Z_][a-zA-Z0-9_]*)\.(\w+)\(([\s\S]*)\)'
        match = re.match(simple_pattern, query_string)
        
        if match:
            collection_name = match.group(1)
            method = match.group(2)
            params = match.group(3)
            return collection_name, method, params
        
        return None, None, ""
    
    def _execute_find(self, collection, params_string: str) -> List[Dict]:
        """Execute a find query"""
        # Parse the parameters
        query, projection, sort, limit = self._parse_find_params(params_string)
        
        cursor = collection.find(query, projection)
        
        if sort:
            cursor = cursor.sort(list(sort.items()))
        
        if limit:
            cursor = cursor.limit(limit)
        
        # Convert results to list and handle ObjectId serialization
        results = []
        for doc in cursor:
            results.append(self._serialize_doc(doc))
        
        return results
    
    def _execute_aggregate(self, collection, params_string: str) -> List[Dict]:
        """Execute an aggregation pipeline"""
        pipeline = self._parse_aggregate_params(params_string)
        
        results = []
        for doc in collection.aggregate(pipeline):
            results.append(self._serialize_doc(doc))
        
        return results
    
    def _execute_count(self, collection, params_string: str) -> int:
        """Execute a count query"""
        query = self._parse_simple_params(params_string)
        return collection.count_documents(query)
    
    def _parse_find_params(self, params_string: str) -> Tuple[Dict, Optional[Dict], Optional[Dict], Optional[int]]:
        """Parse find query parameters"""
        # This is a simplified parser - in production, use a proper JS parser
        query = {}
        projection = None
        sort = None
        limit = None
        
        try:
            # Handle sort and limit chaining
            sort_match = re.search(r'\.sort\((\{[^}]+\})\)', params_string)
            limit_match = re.search(r'\.limit\((\d+)\)', params_string)
            
            if sort_match:
                sort = eval(sort_match.group(1))
                params_string = params_string[:sort_match.start()]
            
            if limit_match:
                limit = int(limit_match.group(1))
                params_string = params_string[:limit_match.start()]
            
            # Parse the main query and projection
            params_string = params_string.strip()
            if params_string:
                # Handle ObjectId and ISODate conversions
                params_string = self._convert_mongo_types(params_string)
                params = eval(params_string)
                
                if isinstance(params, tuple) and len(params) >= 1:
                    query = params[0] if params[0] else {}
                    projection = params[1] if len(params) > 1 else None
                elif isinstance(params, dict):
                    query = params
        except Exception as e:
            print(f"Warning: Could not parse find params: {e}")
        
        return query, projection, sort, limit
    
    def _parse_aggregate_params(self, params_string: str) -> List[Dict]:
        """Parse aggregation pipeline parameters"""
        try:
            params_string = self._convert_mongo_types(params_string)
            pipeline = eval(params_string)
            if isinstance(pipeline, list):
                return pipeline
            return [pipeline]
        except Exception as e:
            print(f"Warning: Could not parse aggregate params: {e}")
            return []
    
    def _parse_simple_params(self, params_string: str) -> Dict:
        """Parse simple query parameters"""
        try:
            params_string = self._convert_mongo_types(params_string)
            return eval(params_string) if params_string.strip() else {}
        except:
            return {}
    
    def _convert_mongo_types(self, query_string: str) -> str:
        """Convert MongoDB-specific types to Python equivalents"""
        # Convert ObjectId
        query_string = re.sub(
            r'ObjectId\(["\']([a-f0-9]{24})["\']\)',
            r'ObjectId("\1")',
            query_string
        )
        
        # Convert ISODate to datetime
        query_string = re.sub(
            r'ISODate\(["\']([^"\']+)["\']\)',
            r'datetime.fromisoformat("\1".replace("Z", "+00:00"))',
            query_string
        )
        
        # Convert new Date
        query_string = re.sub(
            r'new Date\(["\']([^"\']+)["\']\)',
            r'datetime.fromisoformat("\1".replace("Z", "+00:00"))',
            query_string
        )
        
        return query_string
    
    def _serialize_doc(self, doc: Dict) -> Dict:
        """Serialize a MongoDB document to JSON-compatible format"""
        serialized = {}
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                serialized[key] = str(value)
            elif isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, dict):
                serialized[key] = self._serialize_doc(value)
            elif isinstance(value, list):
                serialized[key] = [
                    self._serialize_doc(item) if isinstance(item, dict) else
                    str(item) if isinstance(item, ObjectId) else
                    item.isoformat() if isinstance(item, datetime) else
                    item
                    for item in value
                ]
            else:
                serialized[key] = value
        return serialized


# Global instance for easy access
mongo_connection = MongoDBConnection()

