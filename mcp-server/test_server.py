"""
Test the Pokemon MCP server tools directly.
"""
import asyncio
import httpx


async def test_pokemon_api():
    """Test direct access to Pokemon API."""
    print("🧪 Testing direct Pokemon API access...")
    
    async with httpx.AsyncClient() as client:
        # Test get pokemon info
        print("\n--- Testing get_pokemon_info with Pikachu ---")
        try:
            response = await client.get("https://pokeapi.co/api/v2/pokemon/pikachu")
            response.raise_for_status()
            data = response.json()
            
            pokemon_info = {
                "id": data.get("id"),
                "name": data.get("name"),
                "height": data.get("height"),
                "weight": data.get("weight"),
                "base_experience": data.get("base_experience"),
                "types": [t["type"]["name"] for t in data.get("types", [])],
                "abilities": [a["ability"]["name"] for a in data.get("abilities", [])],
                "stats": {stat["stat"]["name"]: stat["base_stat"] for stat in data.get("stats", [])},
            }
            
            print(f"✅ Pokemon info: {pokemon_info}")
        except Exception as e:
            print(f"❌ Error getting Pokemon info: {e}")
        
        # Test get pokemon species
        print("\n--- Testing get_pokemon_species with Pikachu ---")
        try:
            response = await client.get("https://pokeapi.co/api/v2/pokemon-species/pikachu")
            response.raise_for_status()
            data = response.json()
            
            species_info = {
                "id": data.get("id"),
                "name": data.get("name"),
                "generation": data.get("generation", {}).get("name"),
                "habitat": data.get("habitat", {}).get("name") if data.get("habitat") else None,
                "color": data.get("color", {}).get("name"),
                "flavor_text_entries": [
                    entry["flavor_text"] 
                    for entry in data.get("flavor_text_entries", [])
                    if entry.get("language", {}).get("name") == "en"
                ][:2]  # Get first 2 English descriptions
            }
            
            print(f"✅ Pokemon species: {species_info}")
        except Exception as e:
            print(f"❌ Error getting Pokemon species: {e}")
        
        # Test search pokemon
        print("\n--- Testing search_pokemon (first 10) ---")
        try:
            response = await client.get("https://pokeapi.co/api/v2/pokemon", params={"limit": 10})
            response.raise_for_status()
            data = response.json()
            
            pokemon_list = [
                {
                    "name": pokemon["name"],
                    "id": pokemon["url"].split("/")[-2]  # Extract ID from URL
                }
                for pokemon in data.get("results", [])
            ]
            
            print(f"✅ Pokemon list: {pokemon_list}")
        except Exception as e:
            print(f"❌ Error searching Pokemon: {e}")


if __name__ == "__main__":
    asyncio.run(test_pokemon_api())