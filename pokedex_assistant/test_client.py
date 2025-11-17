#!/usr/bin/env python3
"""
Test client for the Pokédx Assistant Agent.
Tests individual functionality before A2A communication.
"""

import asyncio
import json
from typing import Dict, Any
import httpx

async def test_assistant_agent():
    """Test the Pokédx Assistant Agent individually."""
    agent_url = "http://localhost:10002"
    
    test_queries = [
        "Compare Pikachu and Raichu stats",
        "How effective is Electric type against Water and Flying types?",
        "Generate interesting trivia about Charizard",
        "Show me the top 5 Pokemon by attack stat",
        "Calculate Fire type effectiveness against Grass type",
        "Tell me fun facts about Eevee",
        "Compare Blastoise vs Venusaur",
        "Which type is most effective against Dragon types?"
    ]
    
    async with httpx.AsyncClient() as client:
        print("🎓 Testing Pokédx Assistant Agent")
        print("=" * 50)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🧪 Test {i}: {query}")
            print("-" * 30)
            
            try:
                response = await client.post(
                    f"{agent_url}/chat",
                    json={"message": query},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print("✅ Success!")
                    print("Response preview:", str(result)[:200] + "..." if len(str(result)) > 200 else str(result))
                else:
                    print(f"❌ HTTP {response.status_code}")
                    print("Response:", response.text[:200])
            
            except asyncio.TimeoutError:
                print("⏰ Request timed out")
            except Exception as e:
                print(f"❌ Error: {e}")
            
            # Small delay between requests
            await asyncio.sleep(1)
        
        print(f"\n🏁 Testing complete!")

async def test_agent_health():
    """Test if the agent is running and healthy."""
    agent_url = "http://localhost:10002"
    
    async with httpx.AsyncClient() as client:
        try:
            # Try to get agent info/health
            response = await client.get(f"{agent_url}/", timeout=10.0)
            print(f"🟢 Agent is running (HTTP {response.status_code})")
            return True
        except Exception as e:
            print(f"🔴 Agent not responding: {e}")
            return False

async def main():
    """Main test function."""
    print("🚀 Starting Pokédx Assistant Agent Tests")
    
    # Check if agent is running
    is_healthy = await test_agent_health()
    
    if is_healthy:
        await test_assistant_agent()
    else:
        print("\n💡 To start the agent, run:")
        print("   uv run uvicorn pokedex_assistant.agent:a2a_app --host localhost --port 10002")

if __name__ == "__main__":
    asyncio.run(main())