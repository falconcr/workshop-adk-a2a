import asyncio
import logging
import os

import httpx
from fastmcp import FastMCP

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

mcp = FastMCP("Pokemon MCP Server 🐾")


@mcp.tool()
def get_pokemon_info(
    pokemon_name: str,
):
    """Use this to get information about a specific Pokemon.

    Args:
        pokemon_name: The name or ID of the Pokemon to get information about (e.g., "pikachu", "25").

    Returns:
        A dictionary containing the Pokemon data, or an error message if the request fails.
    """
    logger.info(
        f"--- 🛠️ Tool: get_pokemon_info called for Pokemon: {pokemon_name} ---"
    )
    try:
        response = httpx.get(
            f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}",
            timeout=30.0
        )
        response.raise_for_status()

        data = response.json()
        
        # Extract relevant information to make it more manageable
        pokemon_info = {
            "id": data.get("id"),
            "name": data.get("name"),
            "height": data.get("height"),
            "weight": data.get("weight"),
            "base_experience": data.get("base_experience"),
            "types": [t["type"]["name"] for t in data.get("types", [])],
            "abilities": [a["ability"]["name"] for a in data.get("abilities", [])],
            "stats": {stat["stat"]["name"]: stat["base_stat"] for stat in data.get("stats", [])},
            "sprite": data.get("sprites", {}).get("front_default"),
        }
        
        logger.info(f"✅ Pokemon API response for {pokemon_name}: {pokemon_info}")
        return pokemon_info
    except httpx.HTTPError as e:
        logger.error(f"❌ Pokemon API request failed: {e}")
        return {"error": f"Pokemon API request failed: {e}"}
    except ValueError:
        logger.error("❌ Invalid JSON response from Pokemon API")
        return {"error": "Invalid JSON response from Pokemon API."}


@mcp.tool()
def get_pokemon_species(
    pokemon_name: str,
):
    """Use this to get species information about a specific Pokemon including description and evolution chain.

    Args:
        pokemon_name: The name or ID of the Pokemon to get species information about.

    Returns:
        A dictionary containing the Pokemon species data, or an error message if the request fails.
    """
    logger.info(
        f"--- 🛠️ Tool: get_pokemon_species called for Pokemon: {pokemon_name} ---"
    )
    try:
        response = httpx.get(
            f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_name.lower()}",
            timeout=30.0
        )
        response.raise_for_status()

        data = response.json()
        
        # Extract relevant species information
        species_info = {
            "id": data.get("id"),
            "name": data.get("name"),
            "generation": data.get("generation", {}).get("name"),
            "habitat": data.get("habitat", {}).get("name") if data.get("habitat") else None,
            "color": data.get("color", {}).get("name"),
            "shape": data.get("shape", {}).get("name"),
            "evolution_chain": data.get("evolution_chain", {}).get("url"),
            "flavor_text_entries": [
                entry["flavor_text"] 
                for entry in data.get("flavor_text_entries", [])
                if entry.get("language", {}).get("name") == "en"
            ][:3]  # Get first 3 English descriptions
        }
        
        logger.info(f"✅ Pokemon Species API response for {pokemon_name}: {species_info}")
        return species_info
    except httpx.HTTPError as e:
        logger.error(f"❌ Pokemon Species API request failed: {e}")
        return {"error": f"Pokemon Species API request failed: {e}"}
    except ValueError:
        logger.error("❌ Invalid JSON response from Pokemon Species API")
        return {"error": "Invalid JSON response from Pokemon Species API."}


@mcp.tool()
def search_pokemon(
    limit: int = 20,
    offset: int = 0,
):
    """Use this to search and list Pokemon with pagination.

    Args:
        limit: Number of Pokemon to return (default: 20, max: 100).
        offset: Number of Pokemon to skip (default: 0).

    Returns:
        A dictionary containing the list of Pokemon, or an error message if the request fails.
    """
    logger.info(
        f"--- 🛠️ Tool: search_pokemon called with limit: {limit}, offset: {offset} ---"
    )
    try:
        # Ensure limit doesn't exceed 100
        limit = min(limit, 100)
        
        response = httpx.get(
            "https://pokeapi.co/api/v2/pokemon",
            params={"limit": limit, "offset": offset},
            timeout=30.0
        )
        response.raise_for_status()

        data = response.json()
        
        # Extract Pokemon list
        pokemon_list = {
            "count": data.get("count"),
            "next": data.get("next"),
            "previous": data.get("previous"),
            "pokemon": [
                {
                    "name": pokemon["name"],
                    "url": pokemon["url"],
                    "id": pokemon["url"].split("/")[-2]  # Extract ID from URL
                }
                for pokemon in data.get("results", [])
            ]
        }
        
        logger.info(f"✅ Pokemon search API response: {len(pokemon_list['pokemon'])} Pokemon found")
        return pokemon_list
    except httpx.HTTPError as e:
        logger.error(f"❌ Pokemon search API request failed: {e}")
        return {"error": f"Pokemon search API request failed: {e}"}
    except ValueError:
        logger.error("❌ Invalid JSON response from Pokemon search API")
        return {"error": "Invalid JSON response from Pokemon search API."}


if __name__ == "__main__":
    logger.info(f"🚀 Pokemon MCP server started on port {os.getenv('PORT', 8080)}")
    # Could also use 'sse' transport, host="0.0.0.0" required for Cloud Run.
    asyncio.run(
        mcp.run_async(
            transport="http",
            host="0.0.0.0",
            port=os.getenv("PORT", 8080),
        )
    )