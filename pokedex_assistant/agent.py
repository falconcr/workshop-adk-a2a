import logging
import os
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams

from a2a.types import AgentSkill, AgentCard, AgentCapabilities

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

# A2A configuration
host = os.getenv("A2A_HOST", "localhost")
port = int(os.getenv("A2A_PORT_ASSISTANT", "10002"))

load_dotenv()

SYSTEM_INSTRUCTION = (
    "You are the Pokédex Assistant, an analytical companion to the Pokemon Agent. "
    "Your specialty is providing deep analytical insights, comparisons, trivia, and educational content about Pokemon. "
    "You can compare Pokemon stats, analyze type effectiveness for battles, generate interesting trivia, "
    "and provide statistical rankings. "
    ""
    "Your tools include: "
    "'compare_pokemon_stats' to compare two Pokemon's base statistics, "
    "'calculate_type_effectiveness' to analyze battle type advantages, "
    "'generate_pokemon_trivia' to create interesting facts and educational content, "
    "and 'get_stat_rankings' to show top performers in specific stats. "
    ""
    "IMPORTANT: You work in collaboration with the Pokemon Agent. When you need basic Pokemon information "
    "that you don't have, you can request it from the Pokemon Agent. Likewise, if users need basic Pokemon "
    "data, direct them to the Pokemon Agent. Your focus is analysis, comparisons, and educational insights. "
    ""
    "Always provide detailed, educational, and enthusiastic responses about Pokemon analytics. "
    "Include specific numbers, percentages, and clear explanations when presenting comparisons or analysis. "
    "If asked about non-Pokemon topics, politely redirect to Pokemon-related analytics and comparisons."
)

logger.info("--- 🔬 Loading Analytics MCP tools from Analytics MCP Server... ---")
logger.info("--- 🎓 Creating ADK Pokédex Assistant Agent... ---")

root = LlmAgent(
    model="gemini-2.5-flash",
    name="pokedex_assistant",
    description="An analytical agent specialized in Pokemon comparisons, trivia, and battle analysis",
    instruction=SYSTEM_INSTRUCTION,
    tools=[
        MCPToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=os.getenv("ANALYTICS_MCP_SERVER_URL", "http://localhost:8081/mcp")
            )
        )
    ],
)

# Define analytics-focused skills
comparison_skill = AgentSkill(
    id='compare_pokemon_stats',
    name='Pokemon Stats Comparison',
    description='Compare base statistics between two Pokemon with detailed analysis',
    tags=['pokemon comparison', 'stats analysis', 'pokemon vs pokemon'],
    examples=[
        'Compare Pikachu vs Raichu', 
        'Which has better stats: Charizard or Blastoise?',
        'Analyze the stat differences between Eevee and its evolutions'
    ],
)

battle_analysis_skill = AgentSkill(
    id='calculate_type_effectiveness',
    name='Battle Type Effectiveness Calculator',
    description='Calculate type effectiveness and battle advantages for strategic analysis',
    tags=['type effectiveness', 'battle analysis', 'pokemon strategy'],
    examples=[
        'How effective is Electric type against Water and Flying?',
        'Calculate Fire type effectiveness against Grass/Poison Pokemon',
        'What types are super effective against Dragon type?'
    ],
)

trivia_skill = AgentSkill(
    id='generate_pokemon_trivia',
    name='Pokemon Trivia Generator',
    description='Generate interesting facts, educational content, and fun trivia about Pokemon',
    tags=['pokemon trivia', 'pokemon facts', 'pokemon education'],
    examples=[
        'Tell me interesting facts about Alakazam',
        'Generate trivia about legendary Pokemon',
        'What are some fun facts about Snorlax?'
    ],
)

rankings_skill = AgentSkill(
    id='get_stat_rankings',
    name='Pokemon Stat Rankings',
    description='Show top-performing Pokemon in specific statistical categories',
    tags=['pokemon rankings', 'top pokemon', 'stat analysis'],
    examples=[
        'Show the fastest Pokemon',
        'Which Pokemon have the highest attack?',
        'Top 5 Pokemon by defense stat'
    ],
)

# A2A Agent Card definition for Pokédex Assistant
assistant_agent_card = AgentCard(
    name='Pokédx Assistant',
    description='Analytical companion specialized in Pokemon comparisons, battle analysis, trivia generation, and statistical insights',
    url=f'http://{host}:{port}/',
    version='1.0.0',
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[comparison_skill, battle_analysis_skill, trivia_skill, rankings_skill],
)

# Make the agent A2A-compatible
a2a_app = to_a2a(root, port=port)

# A2A Agent Discovery and Communication
class PokedexAssistantA2A:
    """Enhanced Pokédx Assistant with A2A communication capabilities."""
    
    def __init__(self, base_agent: LlmAgent):
        self.base_agent = base_agent
        self.pokemon_agent: Optional[RemoteA2aAgent] = None
        self.pokemon_agent_url = os.getenv("POKEMON_AGENT_URL", "http://localhost:10001")
        
    async def discover_pokemon_agent(self):
        """Discover and connect to the Pokemon Agent."""
        try:
            logger.info(f"🔍 Discovering Pokemon Agent at {self.pokemon_agent_url}")
            self.pokemon_agent = RemoteA2aAgent(url=self.pokemon_agent_url)
            logger.info("✅ Successfully connected to Pokemon Agent")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Could not connect to Pokemon Agent: {e}")
            return False
    
    async def request_pokemon_info(self, pokemon_name: str) -> str:
        """Request basic Pokemon information from the Pokemon Agent."""
        if not self.pokemon_agent:
            await self.discover_pokemon_agent()
        
        if self.pokemon_agent:
            try:
                logger.info(f"📋 Requesting info for: {pokemon_name}")
                result = await self.pokemon_agent.execute_task(
                    f"Tell me about {pokemon_name}"
                )
                return result
            except Exception as e:
                logger.error(f"❌ Failed to get Pokemon info: {e}")
                return f"I couldn't get information from the Pokemon agent. Error: {e}"
        
        return "The Pokemon Agent is not available for basic information right now."
    
    async def enhanced_analysis_with_collaboration(self, query: str) -> str:
        """Provide enhanced analysis by collaborating with Pokemon Agent when needed."""
        if not self.pokemon_agent:
            await self.discover_pokemon_agent()
        
        # Check if we need basic Pokemon data first
        if any(phrase in query.lower() for phrase in ["tell me about", "what is", "describe"]):
            # Get basic info first, then analyze
            try:
                pokemon_name = self._extract_pokemon_name(query)
                if pokemon_name:
                    basic_info = await self.request_pokemon_info(pokemon_name)
                    return f"Here's the basic info from Pokemon Agent:\n{basic_info}\n\nNow let me provide analytical insights..."
            except Exception as e:
                logger.error(f"❌ Failed collaboration: {e}")
        
        return "Processing analysis with available tools..."
    
    def _extract_pokemon_name(self, query: str) -> Optional[str]:
        """Simple extraction of Pokemon name from query."""
        # This is a basic implementation - in production, you'd use more sophisticated NLP
        words = query.lower().split()
        common_pokemon = ["pikachu", "charizard", "blastoise", "venusaur", "mew", "mewtwo", "eevee", "raichu"]
        for word in words:
            if word in common_pokemon:
                return word.capitalize()
        return None

# Create enhanced assistant with A2A capabilities
assistant_a2a = PokedexAssistantA2A(root)

# ADK expects a variable named 'root_agent'
root_agent = root