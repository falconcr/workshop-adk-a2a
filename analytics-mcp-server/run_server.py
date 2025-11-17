#!/usr/bin/env python3
"""
Standalone runner for the Analytics MCP Server.
Run this to start the analytics server.
"""

import asyncio
import os
import logging
from server import mcp

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info(f"🔬 Analytics MCP server starting on port {os.getenv('PORT', 8081)}")
    asyncio.run(
        mcp.run_async(
            transport="http",
            host="0.0.0.0",
            port=int(os.getenv("PORT", 8081)),
        )
    )