#!/usr/bin/env python3
"""
HTTP-based Analytics MCP Server for Pokemon data analysis and comparisons.
Provides tools for statistical analysis, comparisons, and fun facts about Pokemon via HTTP transport.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("analytics-mcp-http-server")

# Base URL for PokeAPI
POKEAPI_BASE_URL = "https://pokeapi.co/api/v2"

class PokemonAnalytics:
    """Class to handle Pokemon analytics and comparisons."""
    
    def __init__(self):
        self.client = httpx.AsyncClient()
        
    async def get_pokemon_data(self, pokemon_name: str) -> Optional[Dict[str, Any]]:
        """Fetch Pokemon data from PokeAPI."""
        try:
            response = await self.client.get(f"{POKEAPI_BASE_URL}/pokemon/{pokemon_name.lower()}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error fetching Pokemon data: {e}")
            return None
    
    async def get_pokemon_species(self, pokemon_name: str) -> Optional[Dict[str, Any]]:
        """Fetch Pokemon species data from PokeAPI."""
        try:
            response = await self.client.get(f"{POKEAPI_BASE_URL}/pokemon-species/{pokemon_name.lower()}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error fetching Pokemon species data: {e}")
            return None

# Create analytics instance
analytics = PokemonAnalytics()

# Create FastAPI app
app = FastAPI(title="Analytics MCP Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create MCP server
server = Server("analytics-mcp-http-server")

# Register tools
@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools."""
    return [
        Tool(
            name="compare_pokemon_stats",
            description="Compare base statistics between two Pokemon with detailed analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "pokemon1": {
                        "type": "string",
                        "description": "Name of the first Pokemon"
                    },
                    "pokemon2": {
                        "type": "string", 
                        "description": "Name of the second Pokemon"
                    }
                },
                "required": ["pokemon1", "pokemon2"]
            }
        ),
        Tool(
            name="calculate_type_effectiveness",
            description="Calculate type effectiveness and provide battle analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "attacking_type": {
                        "type": "string",
                        "description": "The attacking Pokemon's type"
                    },
                    "defending_type": {
                        "type": "string",
                        "description": "The defending Pokemon's type"
                    }
                },
                "required": ["attacking_type", "defending_type"]
            }
        ),
        Tool(
            name="generate_pokemon_trivia",
            description="Generate interesting trivia and fun facts about a Pokemon",
            inputSchema={
                "type": "object",
                "properties": {
                    "pokemon_name": {
                        "type": "string",
                        "description": "Name of the Pokemon"
                    }
                },
                "required": ["pokemon_name"]
            }
        ),
        Tool(
            name="get_stat_rankings",
            description="Get stat rankings and comparisons for a specific stat across multiple Pokemon",
            inputSchema={
                "type": "object",
                "properties": {
                    "stat_name": {
                        "type": "string",
                        "description": "The stat to analyze (hp, attack, defense, special-attack, special-defense, speed)"
                    },
                    "pokemon_list": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of Pokemon names to compare"
                    }
                },
                "required": ["stat_name", "pokemon_list"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    try:
        if name == "compare_pokemon_stats":
            return await compare_pokemon_stats(arguments)
        elif name == "calculate_type_effectiveness":
            return await calculate_type_effectiveness(arguments)
        elif name == "generate_pokemon_trivia":
            return await generate_pokemon_trivia(arguments)
        elif name == "get_stat_rankings":
            return await get_stat_rankings(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"Tool execution failed: {str(e)}"}, indent=2)
        )]

async def compare_pokemon_stats(arguments: Dict[str, Any]) -> List[TextContent]:
    """Compare statistics between two Pokemon."""
    pokemon1_name = arguments["pokemon1"]
    pokemon2_name = arguments["pokemon2"]
    
    # Fetch data for both Pokemon
    pokemon1_data = await analytics.get_pokemon_data(pokemon1_name)
    pokemon2_data = await analytics.get_pokemon_data(pokemon2_name)
    
    if not pokemon1_data or not pokemon2_data:
        error_msg = f"Could not fetch data for one or both Pokemon: {pokemon1_name}, {pokemon2_name}"
        return [TextContent(type="text", text=json.dumps({"error": error_msg}, indent=2))]
    
    # Extract stats
    pokemon1_stats = {stat["stat"]["name"]: stat["base_stat"] for stat in pokemon1_data["stats"]}
    pokemon2_stats = {stat["stat"]["name"]: stat["base_stat"] for stat in pokemon2_data["stats"]}
    
    # Calculate comparison
    comparison = {
        "pokemon1": {
            "name": pokemon1_data["name"].capitalize(),
            "stats": pokemon1_stats,
            "total_stats": sum(pokemon1_stats.values())
        },
        "pokemon2": {
            "name": pokemon2_data["name"].capitalize(),
            "stats": pokemon2_stats,
            "total_stats": sum(pokemon2_stats.values())
        },
        "differences": {},
        "winner_by_stat": {}
    }
    
    # Compare each stat
    for stat_name in pokemon1_stats:
        diff = pokemon1_stats[stat_name] - pokemon2_stats[stat_name]
        comparison["differences"][stat_name] = diff
        if diff > 0:
            comparison["winner_by_stat"][stat_name] = pokemon1_data["name"].capitalize()
        elif diff < 0:
            comparison["winner_by_stat"][stat_name] = pokemon2_data["name"].capitalize()
        else:
            comparison["winner_by_stat"][stat_name] = "Tie"
    
    return [TextContent(
        type="text",
        text=json.dumps(comparison, indent=2)
    )]

async def calculate_type_effectiveness(arguments: Dict[str, Any]) -> List[TextContent]:
    """Calculate type effectiveness for battle analysis."""
    attacking_type = arguments["attacking_type"].lower()
    defending_type = arguments["defending_type"].lower()
    
    # Type effectiveness chart (simplified)
    type_effectiveness = {
        "fire": {"grass": 2.0, "water": 0.5, "fire": 0.5},
        "water": {"fire": 2.0, "grass": 0.5, "water": 0.5},
        "grass": {"water": 2.0, "fire": 0.5, "grass": 0.5},
        "electric": {"water": 2.0, "grass": 0.5, "electric": 0.5, "ground": 0.0},
        "psychic": {"fighting": 2.0, "psychic": 0.5},
        "fighting": {"normal": 2.0, "psychic": 0.5},
        "normal": {"fighting": 0.5}
    }
    
    effectiveness = type_effectiveness.get(attacking_type, {}).get(defending_type, 1.0)
    
    result = {
        "attacking_type": attacking_type.capitalize(),
        "defending_type": defending_type.capitalize(),
        "effectiveness_multiplier": effectiveness,
        "description": ""
    }
    
    if effectiveness == 2.0:
        result["description"] = f"{attacking_type.capitalize()} is super effective against {defending_type.capitalize()}!"
    elif effectiveness == 0.5:
        result["description"] = f"{attacking_type.capitalize()} is not very effective against {defending_type.capitalize()}."
    elif effectiveness == 0.0:
        result["description"] = f"{attacking_type.capitalize()} has no effect on {defending_type.capitalize()}."
    else:
        result["description"] = f"{attacking_type.capitalize()} deals normal damage to {defending_type.capitalize()}."
    
    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]

async def generate_pokemon_trivia(arguments: Dict[str, Any]) -> List[TextContent]:
    """Generate trivia and fun facts about a Pokemon."""
    pokemon_name = arguments["pokemon_name"]
    
    # Fetch Pokemon data
    pokemon_data = await analytics.get_pokemon_data(pokemon_name)
    species_data = await analytics.get_pokemon_species(pokemon_name)
    
    if not pokemon_data:
        error_msg = f"Could not fetch data for Pokemon: {pokemon_name}"
        return [TextContent(type="text", text=json.dumps({"error": error_msg}, indent=2))]
    
    trivia = {
        "name": pokemon_data["name"].capitalize(),
        "height": pokemon_data["height"] / 10,  # Convert decimeters to meters
        "weight": pokemon_data["weight"] / 10,  # Convert hectograms to kg
        "types": [t["type"]["name"].capitalize() for t in pokemon_data["types"]],
        "abilities": [a["ability"]["name"].replace("-", " ").title() for a in pokemon_data["abilities"]],
        "base_experience": pokemon_data["base_experience"],
        "fun_facts": []
    }
    
    # Add fun facts
    if trivia["height"] > 5:
        trivia["fun_facts"].append(f"This Pokemon is quite tall at {trivia['height']} meters!")
    if trivia["weight"] > 100:
        trivia["fun_facts"].append(f"This Pokemon is heavy, weighing {trivia['weight']} kg!")
    
    if species_data:
        # Add species-specific trivia
        if "flavor_text_entries" in species_data:
            english_entries = [entry for entry in species_data["flavor_text_entries"] if entry["language"]["name"] == "en"]
            if english_entries:
                trivia["description"] = english_entries[0]["flavor_text"].replace("\n", " ")
    
    return [TextContent(
        type="text",
        text=json.dumps(trivia, indent=2)
    )]

async def get_stat_rankings(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get stat rankings for multiple Pokemon."""
    stat_name = arguments["stat_name"]
    pokemon_list = arguments["pokemon_list"]
    
    rankings = []
    
    for pokemon_name in pokemon_list:
        pokemon_data = await analytics.get_pokemon_data(pokemon_name)
        if pokemon_data:
            stats = {stat["stat"]["name"]: stat["base_stat"] for stat in pokemon_data["stats"]}
            if stat_name in stats:
                rankings.append({
                    "name": pokemon_data["name"].capitalize(),
                    stat_name: stats[stat_name]
                })
    
    # Sort by the specified stat (highest first)
    rankings.sort(key=lambda x: x[stat_name], reverse=True)
    
    # Add ranking positions
    for i, pokemon in enumerate(rankings):
        pokemon["rank"] = i + 1
    
    result = {
        "stat_analyzed": stat_name.replace("-", " ").title(),
        "rankings": rankings,
        "summary": {
            "highest": rankings[0] if rankings else None,
            "lowest": rankings[-1] if rankings else None,
            "average": statistics.mean([p[stat_name] for p in rankings]) if rankings else 0
        }
    }
    
    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]

# Create FastAPI MCP server
mcp_app = FastApiMcpServer(server)

# Mount MCP endpoints
app.mount("/mcp", mcp_app.app)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Analytics MCP HTTP Server is running!", "mcp_endpoint": "/mcp"}

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "server": "analytics-mcp-http-server"}

if __name__ == "__main__":
    import uvicorn
    logger.info("🔬 Starting Analytics MCP HTTP Server...")
    logger.info("Available tools: compare_pokemon_stats, calculate_type_effectiveness, generate_pokemon_trivia, get_stat_rankings")
    uvicorn.run(app, host="localhost", port=8081)