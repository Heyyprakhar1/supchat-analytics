import os
import asyncpg
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
from datetime import datetime
import logging

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

# MCP Server Configuration
MCP_SERVER_COMMAND = os.getenv("MCP_SERVER_COMMAND", "npx")
MCP_SERVER_ARGS = os.getenv("MCP_SERVER_ARGS", "-y @modelcontextprotocol/server-postgres").split()

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

async def get_mcp_tools():
    """Connect to MCP server and get available tools"""
    server_params = StdioServerParameters(
        command=MCP_SERVER_COMMAND,
        args=MCP_SERVER_ARGS,
        env={"DATABASE_URL": os.getenv("DATABASE_URL")}
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            return tools

async def natural_language_to_sql(question: str) -> dict:
    """
    Convert natural language to SQL using MCP or fallback to rule-based
    In production, this would use Claude/Cursor via MCP
    """
    # Simplified NL to SQL for demo (replace with actual MCP call)
    question_lower = question.lower()
    
    if "trending topics" in question_lower:
        return {
            "sql": """
                SELECT topic, COUNT(*) as article_count, SUM(views) as total_views 
                FROM articles 
                WHERE created_at > NOW() - INTERVAL '30 days' 
                GROUP BY topic 
                ORDER BY total_views DESC 
                LIMIT 10
            """,
            "chart_type": "bar",
            "explanation": "Top trending topics by views in last 30 days"
        }
    elif "engagement by topic" in question_lower:
        return {
            "sql": """
                SELECT topic, 
                       AVG(likes) as avg_likes, 
                       AVG(shares) as avg_shares,
                       AVG(comments) as avg_comments
                FROM articles 
                GROUP BY topic
            """,
            "chart_type": "bar",
            "explanation": "Average engagement metrics by topic"
        }
    elif "daily views" in question_lower and "ai" in question_lower:
        return {
            "sql": """
                SELECT DATE(created_at) as date, SUM(views) as daily_views
                FROM articles 
                WHERE topic ILIKE '%ai%' 
                AND created_at > NOW() - INTERVAL '30 days'
                GROUP BY DATE(created_at)
                ORDER BY date
            """,
            "chart_type": "line",
            "explanation": "Daily views trend for AI articles"
        }
    else:
        # Generic query
        return {
            "sql": "SELECT * FROM articles LIMIT 10",
            "chart_type": "table",
            "explanation": "Sample articles data"
        }

@app.post("/api/query", response_model=QueryResponse)
async def query_database(req: QueryRequest):
    try:
        # Convert NL to SQL
        query_plan = await natural_language_to_sql(req.question)
        
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
    """Get recent queries (simplified - in production use Redis/DB)"""
    return {"history": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

