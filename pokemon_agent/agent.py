import logging
import os
from typing import Optional

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
port = int(os.getenv("A2A_PORT", "10001"))

load_dotenv()

SYSTEM_INSTRUCTION = (
    "You are a specialized Pokemon assistant. "
    "Your purpose is to help users learn about Pokemon using the available tools: "
    "'get_pokemon_info' to get detailed information about a specific Pokemon, "
    "'get_pokemon_species' to get species information and descriptions, "
    "and 'search_pokemon' to list and find Pokemon. "
    "You can provide information about Pokemon stats, abilities, types, evolution, "
    "descriptions, and help users discover new Pokemon. "
    ""
    "IMPORTANT: When users ask for comparisons, analysis, trivia, or battle effectiveness, "
    "you should suggest they contact the Pokédx Assistant Agent which specializes in "
    "Pokemon analysis and comparisons. You can also collaborate with the assistant agent "
    "to provide more comprehensive responses. "
    ""
    "If the user asks about anything completely unrelated to Pokemon, "
    "politely state that you can only assist with Pokemon-related queries. "
    "Always be enthusiastic and helpful when discussing Pokemon!"
)

logger.info("--- 🔧 Loading MCP tools from Pokemon MCP Server... ---")
logger.info("--- 🤖 Creating ADK Pokemon Agent... ---")

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="pokemon_agent",
    description="An agent that can help with Pokemon information and discovery",
    instruction=SYSTEM_INSTRUCTION,
    tools=[
        MCPToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=os.getenv("MCP_SERVER_URL", "http://localhost:8080/mcp")
            )
        )
    ],
)

# Define Pokemon-related skills
pokemon_info_skill = AgentSkill(
    id='get_pokemon_info',
    name='Pokemon Information Tool',
    description='Get detailed information about a specific Pokemon including stats, abilities, and types',
    tags=['pokemon info', 'pokemon stats', 'pokemon abilities'],
    examples=['Tell me about Pikachu', 'What are the stats for Charizard?'],
)

pokemon_species_skill = AgentSkill(
    id='get_pokemon_species',
    name='Pokemon Species Tool',
    description='Get species information about Pokemon including descriptions and evolution details',
    tags=['pokemon species', 'pokemon description', 'pokemon evolution'],
    examples=['What is the description of Bulbasaur?', 'Tell me about Eevee evolution'],
)

pokemon_search_skill = AgentSkill(
    id='search_pokemon',
    name='Pokemon Search Tool',
    description='Search and list Pokemon with pagination to discover new Pokemon',
    tags=['pokemon search', 'pokemon list', 'discover pokemon'],
    examples=['Show me a list of Pokemon', 'Find Pokemon starting from number 100'],
)

# A2A Agent Card definition
agent_card = AgentCard(
    name='Pokemon Agent',
    description='Helps with Pokemon information, stats, descriptions, and discovery using the PokeAPI',
    url=f'http://{host}:{port}/',
    version='1.0.0',
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[pokemon_info_skill, pokemon_species_skill, pokemon_search_skill],
)

# A2A Agent Discovery and Communication
class PokemonAgentA2A:
    """Enhanced Pokemon Agent with A2A communication capabilities."""
    
    def __init__(self, base_agent: LlmAgent):
        self.base_agent = base_agent
        self.assistant_agent: Optional[RemoteA2aAgent] = None
        self.assistant_url = os.getenv("ASSISTANT_AGENT_URL", "http://localhost:10002")
        
    async def discover_assistant_agent(self):
        """Discover and connect to the Pokédx Assistant Agent."""
        try:
            logger.info(f"🔍 Discovering Pokédx Assistant Agent at {self.assistant_url}")
            self.assistant_agent = RemoteA2aAgent(url=self.assistant_url)
            logger.info("✅ Successfully connected to Pokédx Assistant Agent")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Could not connect to Pokédx Assistant Agent: {e}")
            return False
    
    async def request_pokemon_comparison(self, pokemon1: str, pokemon2: str) -> str:
        """Request a Pokemon comparison from the Assistant Agent."""
        if not self.assistant_agent:
            await self.discover_assistant_agent()
        
        if self.assistant_agent:
            try:
                logger.info(f"📊 Requesting comparison: {pokemon1} vs {pokemon2}")
                result = await self.assistant_agent.execute_task(
                    f"Compare {pokemon1} and {pokemon2} stats in detail"
                )
                return result
            except Exception as e:
                logger.error(f"❌ Failed to get comparison: {e}")
                return f"I couldn't get the comparison from the assistant agent. Error: {e}"
        
        return "The Pokédx Assistant Agent is not available for comparisons right now."
    
    async def request_pokemon_trivia(self, pokemon_name: str) -> str:
        """Request Pokemon trivia from the Assistant Agent."""
        if not self.assistant_agent:
            await self.discover_assistant_agent()
        
        if self.assistant_agent:
            try:
                logger.info(f"🎯 Requesting trivia for: {pokemon_name}")
                result = await self.assistant_agent.execute_task(
                    f"Generate interesting trivia and facts about {pokemon_name}"
                )
                return result
            except Exception as e:
                logger.error(f"❌ Failed to get trivia: {e}")
                return f"I couldn't get trivia from the assistant agent. Error: {e}"
        
        return "The Pokédx Assistant Agent is not available for trivia right now."

# Create enhanced agent with A2A capabilities
pokemon_a2a = PokemonAgentA2A(root_agent)

# Make the agent A2A-compatible
a2a_app = to_a2a(root_agent, port=port)