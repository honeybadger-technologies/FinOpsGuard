"""
Main entry point for FinOpsGuard
"""

import uvicorn
import os
import logging
from .api.server import create_app

logger = logging.getLogger(__name__)

# Initialize database on module load
try:
    from .database import init_db
    init_db()
except Exception as e:
    logger.warning(f"Database initialization failed: {e}. Using in-memory storage.")

app = create_app()


def main():
    """Run the FinOpsGuard server"""
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"FinOpsGuard MCP listening on {host}:{port}")
    
    uvicorn.run(
        "finopsguard.main:app",
        host=host,
        port=port,
        reload=os.environ.get("NODE_ENV") == "development"
    )


if __name__ == "__main__":
    main()
