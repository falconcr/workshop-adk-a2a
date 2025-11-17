#!/usr/bin/env python3
"""
Analytics MCP Server for Pokemon data analysis and comparisons.
Provides tools for statistical analysis, comparisons, and fun facts about Pokemon.
"""

import asyncio
import logging
import os
import statistics
from typing import Dict, List, Any, Optional
import httpx
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

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
    
    async def compare_pokemon_stats(self, pokemon1: str, pokemon2: str) -> Dict[str, Any]:
        """Compare stats between two Pokemon."""
        data1 = await self.get_pokemon_data(pokemon1)
        data2 = await self.get_pokemon_data(pokemon2)
        
        if not data1 or not data2:
            return {"error": f"Could not find data for one or both Pokemon: {pokemon1}, {pokemon2}"}
        
        stats1 = {stat['stat']['name']: stat['base_stat'] for stat in data1['stats']}
        stats2 = {stat['stat']['name']: stat['base_stat'] for stat in data2['stats']}
        
        comparison = {
            "pokemon1": {
                "name": data1['name'].title(),
                "stats": stats1,
                "total": sum(stats1.values()),
                "types": [t['type']['name'] for t in data1['types']]
            },
            "pokemon2": {
                "name": data2['name'].title(),
                "stats": stats2,
                "total": sum(stats2.values()),
                "types": [t['type']['name'] for t in data2['types']]
            },
            "comparison": {}
        }
        
        # Compare individual stats
        for stat_name in stats1.keys():
            diff = stats1[stat_name] - stats2[stat_name]
            winner = pokemon1 if diff > 0 else pokemon2 if diff < 0 else "tie"
            comparison["comparison"][stat_name] = {
                "difference": abs(diff),
                "winner": winner
            }
        
        # Overall winner
        total_diff = comparison["pokemon1"]["total"] - comparison["pokemon2"]["total"]
        comparison["overall_winner"] = pokemon1 if total_diff > 0 else pokemon2 if total_diff < 0 else "tie"
        
        return comparison
    
    async def get_type_effectiveness(self, attacker_type: str, defender_types: List[str]) -> Dict[str, Any]:
        """Calculate type effectiveness for battle analysis."""
        try:
            response = await self.client.get(f"{POKEAPI_BASE_URL}/type/{attacker_type.lower()}")
            if response.status_code != 200:
                return {"error": f"Type '{attacker_type}' not found"}
            
            type_data = response.json()
            damage_relations = type_data["damage_relations"]
            
            effectiveness = 1.0
            details = []
            
            for defender_type in defender_types:
                # Check for super effective
                if any(t["name"] == defender_type.lower() for t in damage_relations["double_damage_to"]):
                    effectiveness *= 2.0
                    details.append(f"Super effective against {defender_type}")
                # Check for not very effective
                elif any(t["name"] == defender_type.lower() for t in damage_relations["half_damage_to"]):
                    effectiveness *= 0.5
                    details.append(f"Not very effective against {defender_type}")
                # Check for no effect
                elif any(t["name"] == defender_type.lower() for t in damage_relations["no_damage_to"]):
                    effectiveness *= 0.0
                    details.append(f"No effect against {defender_type}")
                else:
                    details.append(f"Normal effectiveness against {defender_type}")
            
            return {
                "attacker_type": attacker_type,
                "defender_types": defender_types,
                "effectiveness_multiplier": effectiveness,
                "description": self._get_effectiveness_description(effectiveness),
                "details": details
            }
        except Exception as e:
            return {"error": f"Error calculating type effectiveness: {e}"}
    
    def _get_effectiveness_description(self, multiplier: float) -> str:
        """Get human-readable effectiveness description."""
        if multiplier >= 4.0:
            return "Extremely effective!"
        elif multiplier >= 2.0:
            return "Super effective!"
        elif multiplier == 1.0:
            return "Normal effectiveness"
        elif multiplier >= 0.5:
            return "Not very effective..."
        elif multiplier > 0:
            return "Barely effective..."
        else:
            return "No effect!"
    
    async def generate_pokemon_trivia(self, pokemon_name: str) -> Dict[str, Any]:
        """Generate interesting trivia about a Pokemon."""
        pokemon_data = await self.get_pokemon_data(pokemon_name)
        species_data = await self.get_pokemon_species(pokemon_name)
        
        if not pokemon_data:
            return {"error": f"Pokemon '{pokemon_name}' not found"}
        
        trivia = {
            "pokemon": pokemon_data['name'].title(),
            "facts": []
        }
        
        # Basic facts
        height_m = pokemon_data['height'] / 10  # Convert decimeters to meters
        weight_kg = pokemon_data['weight'] / 10  # Convert hectograms to kilograms
        
        trivia["facts"].append(f"Height: {height_m}m, Weight: {weight_kg}kg")
        
        # Stats analysis
        stats = {stat['stat']['name']: stat['base_stat'] for stat in pokemon_data['stats']}
        highest_stat = max(stats, key=stats.get)
        lowest_stat = min(stats, key=stats.get)
        total_stats = sum(stats.values())
        
        trivia["facts"].append(f"Highest stat: {highest_stat.replace('-', ' ').title()} ({stats[highest_stat]})")
        trivia["facts"].append(f"Lowest stat: {lowest_stat.replace('-', ' ').title()} ({stats[lowest_stat]})")
        trivia["facts"].append(f"Total base stats: {total_stats}")
        
        # Type information
        types = [t['type']['name'] for t in pokemon_data['types']]
        if len(types) == 1:
            trivia["facts"].append(f"Pure {types[0].title()}-type Pokemon")
        else:
            trivia["facts"].append(f"Dual-type: {' and '.join([t.title() for t in types])}")
        
        # Abilities
        abilities = [a['ability']['name'].replace('-', ' ').title() for a in pokemon_data['abilities']]
        trivia["facts"].append(f"Abilities: {', '.join(abilities)}")
        
        # Species info if available
        if species_data:
            # Find English flavor text
            for entry in species_data.get('flavor_text_entries', []):
                if entry['language']['name'] == 'en':
                    flavor_text = entry['flavor_text'].replace('\n', ' ').replace('\f', ' ')
                    trivia["facts"].append(f"Pokedex entry: {flavor_text}")
                    break
            
            # Generation info
            generation = species_data.get('generation', {}).get('name', '').replace('generation-', 'Generation ').upper()
            if generation:
                trivia["facts"].append(f"First appeared in: {generation}")
        
        return trivia
    
    async def get_stat_rankings(self, stat_name: str, limit: int = 10) -> Dict[str, Any]:
        """Get top Pokemon by a specific stat (simplified version)."""
        # Note: This is a simplified implementation. In a real scenario, you'd want to 
        # cache or pre-calculate this data as it requires many API calls
        
        rankings = {
            "stat": stat_name.replace('-', ' ').title(),
            "note": "This is a sample ranking. Full rankings would require extensive API calls.",
            "sample_high_performers": []
        }
        
        # Sample high performers for different stats (pre-known data)
        sample_data = {
            "hp": [
                {"name": "Blissey", "value": 255},
                {"name": "Chansey", "value": 250},
                {"name": "Wobbuffet", "value": 190},
                {"name": "Wigglytuff", "value": 140},
                {"name": "Vaporeon", "value": 130}
            ],
            "attack": [
                {"name": "Mega Mewtwo X", "value": 190},
                {"name": "Groudon", "value": 180},
                {"name": "Kyogre", "value": 180},
                {"name": "Rayquaza", "value": 180},
                {"name": "Dialga", "value": 170}
            ],
            "defense": [
                {"name": "Shuckle", "value": 230},
                {"name": "Mega Steelix", "value": 230},
                {"name": "Mega Aggron", "value": 230},
                {"name": "Regirock", "value": 200},
                {"name": "Cloyster", "value": 180}
            ],
            "speed": [
                {"name": "Ninjask", "value": 160},
                {"name": "Deoxys Speed", "value": 180},
                {"name": "Electrode", "value": 150},
                {"name": "Aerodactyl", "value": 130},
                {"name": "Crobat", "value": 130}
            ]
        }
        
        stat_key = stat_name.lower().replace(' ', '-')
        if stat_key in sample_data:
            rankings["sample_high_performers"] = sample_data[stat_key][:limit]
        else:
            rankings["note"] += f" Stat '{stat_name}' not found in sample data."
        
        return rankings

# Create FastMCP instance
mcp = FastMCP("Analytics MCP Server 🔬")
analytics = PokemonAnalytics()

@mcp.tool()
async def compare_pokemon_stats(
    pokemon1: str,
    pokemon2: str,
):
    """Compare base stats between two Pokemon.
    
    Args:
        pokemon1: Name of the first Pokemon
        pokemon2: Name of the second Pokemon
        
    Returns:
        A comparison of base stats between the two Pokemon.
    """
    logger.info(f"--- 🛠️ Tool: compare_pokemon_stats called for {pokemon1} vs {pokemon2} ---")
    
    result = await analytics.compare_pokemon_stats(pokemon1, pokemon2)
    logger.info(f"✅ Pokemon comparison result: {result}")
    return result


@mcp.tool()
async def calculate_type_effectiveness(
    attacker_type: str,
    defender_types: List[str],
):
    """Calculate type effectiveness for battle analysis.
    
    Args:
        attacker_type: The attacking Pokemon's type
        defender_types: List of defending Pokemon's types
        
    Returns:
        Type effectiveness calculation with multiplier and description.
    """
    logger.info(f"--- 🛠️ Tool: calculate_type_effectiveness called for {attacker_type} vs {defender_types} ---")
    
    result = await analytics.get_type_effectiveness(attacker_type, defender_types)
    logger.info(f"✅ Type effectiveness result: {result}")
    return result


@mcp.tool()
async def generate_pokemon_trivia(
    pokemon_name: str,
):
    """Generate interesting trivia and facts about a Pokemon.
    
    Args:
        pokemon_name: Name of the Pokemon to generate trivia for
        
    Returns:
        Interesting trivia and facts about the Pokemon.
    """
    logger.info(f"--- 🛠️ Tool: generate_pokemon_trivia called for {pokemon_name} ---")
    
    result = await analytics.generate_pokemon_trivia(pokemon_name)
    logger.info(f"✅ Pokemon trivia result: {result}")
    return result


@mcp.tool()
async def get_stat_rankings(
    stat_name: str,
    limit: int = 10,
):
    """Get top Pokemon by a specific stat.
    
    Args:
        stat_name: Name of the stat (hp, attack, defense, special-attack, special-defense, speed)
        limit: Number of top Pokemon to return (default: 10, max: 20)
        
    Returns:
        Rankings of top Pokemon for the specified stat.
    """
    logger.info(f"--- 🛠️ Tool: get_stat_rankings called for {stat_name} with limit {limit} ---")
    
    result = await analytics.get_stat_rankings(stat_name, min(limit, 20))
    logger.info(f"✅ Stat rankings result: {result}")
    return result


if __name__ == "__main__":
    logger.info(f"🔬 Analytics MCP server started on port {os.getenv('PORT', 8081)}")
    logger.info("Available tools: compare_pokemon_stats, calculate_type_effectiveness, generate_pokemon_trivia, get_stat_rankings")
    asyncio.run(
        mcp.run_async(
            transport="http",
            host="0.0.0.0",
            port=os.getenv("PORT", 8081),
        )
    )