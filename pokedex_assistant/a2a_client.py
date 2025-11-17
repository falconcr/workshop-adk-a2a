#!/usr/bin/env python3
"""
A2A Communication Client for Pokemon Agent and Pokédex Assistant Agent.
Demonstrates inter-agent communication and collaboration.
"""

import asyncio
import json
from typing import Dict, Any
import httpx

class PokemonA2AClient:
    """Client to demonstrate A2A communication between Pokemon Agent and Pokédx Assistant."""
    
    def __init__(self):
        self.pokemon_agent_url = "http://localhost:10001"
        self.assistant_agent_url = "http://localhost:10002"
        self.client = httpx.AsyncClient()
    
    async def query_pokemon_agent(self, message: str) -> Dict[str, Any]:
        """Send a query to the Pokemon Agent."""
        try:
            response = await self.client.post(
                f"{self.pokemon_agent_url}/chat",
                json={"message": message},
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Pokemon Agent returned status {response.status_code}"}
        except Exception as e:
            return {"error": f"Failed to contact Pokemon Agent: {e}"}
    
    async def query_assistant_agent(self, message: str) -> Dict[str, Any]:
        """Send a query to the Pokédx Assistant Agent."""
        try:
            response = await self.client.post(
                f"{self.assistant_agent_url}/chat",
                json={"message": message},
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Assistant Agent returned status {response.status_code}"}
        except Exception as e:
            return {"error": f"Failed to contact Assistant Agent: {e}"}
    
    async def collaborative_analysis(self, pokemon1: str, pokemon2: str) -> Dict[str, Any]:
        """Demonstrate collaborative analysis between both agents."""
        print(f"\n🤝 Starting collaborative analysis: {pokemon1} vs {pokemon2}")
        
        # Step 1: Get basic info from Pokemon Agent
        print(f"📋 Step 1: Getting {pokemon1} info from Pokemon Agent...")
        pokemon1_info = await self.query_pokemon_agent(f"Tell me about {pokemon1}")
        
        print(f"📋 Step 2: Getting {pokemon2} info from Pokemon Agent...")
        pokemon2_info = await self.query_pokemon_agent(f"Tell me about {pokemon2}")
        
        # Step 3: Get analytical comparison from Assistant Agent
        print(f"🔬 Step 3: Getting detailed comparison from Pokédx Assistant...")
        comparison = await self.query_assistant_agent(f"Compare {pokemon1} and {pokemon2} stats")
        
        # Step 4: Get battle analysis from Assistant Agent
        print(f"⚔️ Step 4: Getting battle analysis from Pokédx Assistant...")
        battle_analysis = await self.query_assistant_agent(
            f"Analyze type effectiveness between {pokemon1} and {pokemon2}"
        )
        
        # Step 5: Get trivia from Assistant Agent
        print(f"🎯 Step 5: Getting trivia from Pokédx Assistant...")
        trivia = await self.query_assistant_agent(f"Generate trivia about {pokemon1}")
        
        return {
            "pokemon1_basic_info": pokemon1_info,
            "pokemon2_basic_info": pokemon2_info,
            "detailed_comparison": comparison,
            "battle_analysis": battle_analysis,
            "trivia": trivia
        }
    
    async def demonstrate_workflows(self):
        """Demonstrate different A2A communication workflows."""
        print("🌟 Pokemon Agent & Pokédx Assistant A2A Demo")
        print("=" * 60)
        
        # Workflow 1: Individual agent queries
        print("\n💫 Workflow 1: Individual Agent Queries")
        print("-" * 40)
        
        # Query Pokemon Agent
        print("🔵 Querying Pokemon Agent for Pikachu info...")
        pikachu_info = await self.query_pokemon_agent("Tell me about Pikachu")
        print("Response:", json.dumps(pikachu_info, indent=2)[:300] + "...")
        
        # Query Assistant Agent
        print("\n🟡 Querying Pokédx Assistant for comparison...")
        comparison = await self.query_assistant_agent("Compare Pikachu and Raichu")
        print("Response:", json.dumps(comparison, indent=2)[:300] + "...")
        
        # Workflow 2: Collaborative analysis
        print("\n\n💫 Workflow 2: Collaborative Analysis")
        print("-" * 40)
        
        collaboration_result = await self.collaborative_analysis("Charizard", "Blastoise")
        print("\n✅ Collaborative analysis complete!")
        print("Full result structure:")
        for key in collaboration_result.keys():
            print(f"  - {key}")
        
        # Workflow 3: Specialized queries
        print("\n\n💫 Workflow 3: Specialized Agent Queries")
        print("-" * 40)
        
        # Pokemon Agent: Search functionality
        print("🔵 Pokemon Agent: Searching for Pokemon...")
        search_result = await self.query_pokemon_agent("Show me the first 5 Pokemon")
        print("Search result keys:", list(search_result.keys()) if isinstance(search_result, dict) else "N/A")
        
        # Assistant Agent: Trivia generation
        print("\n🟡 Pokédx Assistant: Generating trivia...")
        trivia_result = await self.query_assistant_agent("Generate interesting facts about Mew")
        print("Trivia result keys:", list(trivia_result.keys()) if isinstance(trivia_result, dict) else "N/A")
        
        # Assistant Agent: Battle analysis
        print("\n🟡 Pokédx Assistant: Battle analysis...")
        battle_result = await self.query_assistant_agent("How effective is Fire against Grass and Water types?")
        print("Battle analysis keys:", list(battle_result.keys()) if isinstance(battle_result, dict) else "N/A")
    
    async def interactive_mode(self):
        """Interactive mode for testing A2A communication."""
        print("\n🎮 Interactive A2A Mode")
        print("Commands:")
        print("  'pokemon <query>' - Send to Pokemon Agent")
        print("  'assistant <query>' - Send to Pokédx Assistant")
        print("  'compare <pokemon1> <pokemon2>' - Collaborative analysis")
        print("  'quit' - Exit")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if user_input.lower() == 'quit':
                    break
                
                if user_input.startswith('pokemon '):
                    query = user_input[8:]
                    print("🔵 Sending to Pokemon Agent...")
                    result = await self.query_pokemon_agent(query)
                    print(json.dumps(result, indent=2))
                
                elif user_input.startswith('assistant '):
                    query = user_input[10:]
                    print("🟡 Sending to Pokédx Assistant...")
                    result = await self.query_assistant_agent(query)
                    print(json.dumps(result, indent=2))
                
                elif user_input.startswith('compare '):
                    parts = user_input[8:].split()
                    if len(parts) >= 2:
                        pokemon1, pokemon2 = parts[0], parts[1]
                        print("🤝 Starting collaborative analysis...")
                        result = await self.collaborative_analysis(pokemon1, pokemon2)
                        print("✅ Analysis complete! Check detailed results above.")
                    else:
                        print("❌ Usage: compare <pokemon1> <pokemon2>")
                
                else:
                    print("❌ Unknown command. Use 'pokemon', 'assistant', 'compare', or 'quit'")
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

async def main():
    """Main function to run the A2A demo."""
    client = PokemonA2AClient()
    
    try:
        # First, run automated demos
        await client.demonstrate_workflows()
        
        # Then, offer interactive mode
        print("\n" + "=" * 60)
        response = input("Would you like to try interactive mode? (y/n): ")
        if response.lower().startswith('y'):
            await client.interactive_mode()
        
        print("\n👋 A2A Demo completed!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())