import os
import asyncpg
import json
import requests
import re
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime
import asyncio

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SupaChat API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database pool
pool: asyncpg.Pool = None

class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    sql: Optional[str]
    data: List[Dict[str, Any]]
    chart_type: Optional[str]
    explanation: str
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: str

async def get_database_schema() -> str:
    """Fetch actual schema from PostgreSQL"""
    global pool
    try:
        async with pool.acquire() as conn:
            tables = await conn.fetch("""
                SELECT table_name, column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
            """)
            
            schema = {}
            for row in tables:
                if row['table_name'] not in schema:
                    schema[row['table_name']] = []
                schema[row['table_name']].append(f"{row['column_name']} ({row['data_type']})")
            
            return "\n".join([f"{table}: {', '.join(cols)}" for table, cols in schema.items()])
    except Exception as e:
        logger.error(f"Schema fetch error: {e}")
        # Fallback to hardcoded if DB not ready
        return "articles: id (integer), title (character varying), topic (character varying), views (integer), likes (integer), shares (integer), created_at (timestamp with time zone)"

def generate_sql_with_ollama(question: str, schema: str) -> dict:
    """Call local Ollama LLM (FREE - no API key!)"""
    
    prompt = f"""You are a PostgreSQL expert. Convert natural language to SQL.

Database Schema:
{schema}

Question: {question}

Rules:
1. Generate ONLY valid PostgreSQL SELECT queries
2. Return ONLY a JSON object with this exact format:
   {{"sql": "SELECT ...", "chart_type": "bar|line|table", "explanation": "brief description"}}
3. Use bar chart for comparisons, line for trends/time series, table for lists
4. Always include LIMIT 50 for safety
5. If the question is unclear, return: {{"sql": "SELECT * FROM articles LIMIT 10", "chart_type": "table", "explanation": "Showing sample data"}}
6. Return ONLY the JSON object, no markdown, no explanation outside JSON

Response (JSON only):"""

    try:
        # Call local Ollama (completely free!)
        response = requests.post(
            "http://ollama:11434/api/generate",
            json={
                "model": "tinyllama",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low creativity = more accurate SQL
                    "num_predict": 500
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result_text = response.json().get("response", "")
            logger.info(f"Ollama response: {result_text}")
            
            # Extract JSON from response (LLM might add markdown)
            json_match = re.search(r'\{[^{}]*\}', result_text, re.DOTALL)
            if not json_match:
                # Try with more complex regex for nested
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    
                    # Validate required keys
                    if not all(k in result for k in ['sql', 'chart_type', 'explanation']):
                        raise ValueError("Missing required keys in response")
                    
                    # Safety checks - prevent destructive queries
                    sql = result.get("sql", "").lower()
                    if any(word in sql for word in ["delete", "drop", "insert", "update", "truncate", "alter"]):
                        logger.warning(f"Blocked dangerous query: {sql}")
                        return {
                            "sql": "SELECT * FROM articles LIMIT 10",
                            "chart_type": "table",
                            "explanation": "Safety fallback: read-only queries only"
                        }
                    
                    # Ensure LIMIT is present for safety
                    if "limit" not in sql:
                        result['sql'] = result['sql'].rstrip(';') + " LIMIT 50"
                    
                    return result
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parse error: {e}, text was: {result_text}")
                    raise Exception("Invalid JSON from Ollama")
        
        raise Exception(f"Ollama error: {response.status_code} - {response.text}")
        
    except Exception as e:
        logger.error(f"Ollama failed: {e}")
        raise e

def mock_sql_fallback(question: str) -> dict:
    """Fallback if Ollama not ready"""
    question_lower = question.lower()
    
    if "trending" in question_lower or "top" in question_lower:
        return {
            "sql": "SELECT topic, SUM(views) as total_views FROM articles GROUP BY topic ORDER BY total_views DESC LIMIT 10",
            "chart_type": "bar",
            "explanation": "Top trending topics by views (fallback mode)"
        }
    elif "engagement" in question_lower:
        return {
            "sql": "SELECT topic, AVG(likes) as avg_likes, AVG(shares) as avg_shares FROM articles GROUP BY topic",
            "chart_type": "bar",
            "explanation": "Average engagement by topic (fallback mode)"
        }
    elif "daily" in question_lower or "trend" in question_lower:
        return {
            "sql": "SELECT DATE(created_at) as date, SUM(views) as daily_views FROM articles GROUP BY DATE(created_at) ORDER BY date",
            "chart_type": "line",
            "explanation": "Daily views trend (fallback mode)"
        }
    else:
        return {
            "sql": "SELECT * FROM articles LIMIT 10",
            "chart_type": "table",
            "explanation": "Sample articles data (fallback mode)"
        }

async def natural_language_to_sql(question: str) -> dict:
    """Main entry point - uses FREE local AI"""
    try:
        # Check if Ollama is available
        try:
            health_check = requests.get("http://ollama:11434/api/tags", timeout=2)
            if health_check.status_code != 200:
                raise Exception("Ollama not ready")
        except:
            logger.warning("Ollama not available, using fallback")
            return mock_sql_fallback(question)
        
        # Get schema and generate SQL
        schema = await get_database_schema()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            lambda: generate_sql_with_ollama(question, schema)
        )
        return result
        
    except Exception as e:
        logger.error(f"NL2SQL error: {e}")
        return mock_sql_fallback(question)

@app.on_event("startup")
async def startup():
    global pool
    try:
        pool = await asyncpg.create_pool(
            os.getenv("DATABASE_URL"),
            min_size=5,
            max_size=20
        )
        logger.info("Database pool created")
    except Exception as e:
        logger.error(f"Failed to create pool: {e}")
        raise

@app.on_event("shutdown")
async def shutdown():
    await pool.close()

@app.post("/api/query", response_model=QueryResponse)
async def query_database(req: QueryRequest):
    try:
        # Convert NL to SQL using Ollama (FREE!)
        query_plan = await natural_language_to_sql(req.question)
        logger.info(f"Generated SQL: {query_plan['sql']}")
        
        # Execute query
        async with pool.acquire() as conn:
            records = await conn.fetch(query_plan["sql"])
            data = [dict(record) for record in records]
        
        return QueryResponse(
            sql=query_plan["sql"],
            data=data,
            chart_type=query_plan["chart_type"],
            explanation=query_plan["explanation"],
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    try:
        async with pool.acquire() as conn:
            await conn.fetch("SELECT 1")
        return HealthResponse(
            status="healthy",
            database="connected",
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            database=str(e),
            timestamp=datetime.utcnow().isoformat()
        )

@app.get("/api/history")
async def get_history():
    """Get recent queries (simplified)"""
    return {"history": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

