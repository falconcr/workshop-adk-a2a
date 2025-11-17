#!/usr/bin/env python3
"""
Test script for the Analytics MCP Server.
"""

import asyncio
import json
from server import PokemonAnalytics

async def test_analytics():
    """Test the analytics functionality."""
    analytics = PokemonAnalytics()
    
    print("🧪 Testing Pokemon Analytics...")
    
    # Test comparison
    print("\n📊 Testing Pokemon Comparison:")
    comparison = await analytics.compare_pokemon_stats("pikachu", "raichu")
    print(json.dumps(comparison, indent=2))
    
    # Test type effectiveness
    print("\n⚔️ Testing Type Effectiveness:")
    effectiveness = await analytics.get_type_effectiveness("electric", ["water", "flying"])
    print(json.dumps(effectiveness, indent=2))
    
    # Test trivia
    print("\n🎯 Testing Pokemon Trivia:")
    trivia = await analytics.generate_pokemon_trivia("charizard")
    print(json.dumps(trivia, indent=2))
    
    # Test stat rankings
    print("\n🏆 Testing Stat Rankings:")
    rankings = await analytics.get_stat_rankings("attack", 5)
    print(json.dumps(rankings, indent=2))
    
    await analytics.client.aclose()

if __name__ == "__main__":
    asyncio.run(test_analytics())