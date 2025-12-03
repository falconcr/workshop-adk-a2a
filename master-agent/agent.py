import logging
import os
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams

from a2a.types import AgentSkill, AgentCard, AgentCapabilities
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.genai import types

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

# A2A configuration for sub-agents
host = os.getenv("A2A_HOST", "localhost")

load_dotenv()

SYSTEM_INSTRUCTION = (
    "You are the Pokemon Master Agent, a coordinator that manages multiple specialized Pokemon agents. "
    "You have access to two specialized agents: "
    ""
    "1. **Pokemon Agent** (prime_agent): Handles basic Pokemon information, stats, descriptions, and discovery. "
    "   Use this for: getting Pokemon info, species data, searching/listing Pokemon. "
    ""
    "2. **Pokedx Assistant** (pokedx_assistant): Specializes in analysis, comparisons, trivia, and battle effectiveness. "
    "   Use this for: comparing Pokemon stats, type effectiveness analysis, trivia generation, stat rankings. "
    ""
    "IMPORTANT: When users ask for: "
    "- Basic Pokemon info, stats, descriptions → delegate to Pokemon Agent "
    "- Comparisons, analysis, trivia, type effectiveness → delegate to Pokedx Assistant "
    ""
    "Always route requests to the appropriate specialist agent and provide comprehensive responses. "
    "You can coordinate between both agents when needed to provide complete answers. "
    "Be enthusiastic about Pokemon and ensure users get the best possible assistance!"
)

logger.info("--- 🎯 Loading Pokemon sub-agents... ---")
logger.info("--- 👑 Creating ADK Pokemon Master Agent... ---")

pokemon_agent = RemoteA2aAgent(
    name="prime_agent",
    description="An agent that can help with Pokemon information and discovery",
    agent_card=(
        f"http://localhost:10001/{AGENT_CARD_WELL_KNOWN_PATH}"
    ),
)

assistant_agent = RemoteA2aAgent(
    name="pokedex_assistant",
    description="An analytical agent specialized in Pokemon comparisons, trivia, and battle analysis",
    agent_card=(
        f"http://localhost:10002/{AGENT_CARD_WELL_KNOWN_PATH}"
    ),
)


root = LlmAgent(
    model="gemini-2.5-flash",
    name="pokemon_master_agent",
    description="Master coordinator for Pokemon information and analysis, managing specialized Pokemon agents",
    instruction=SYSTEM_INSTRUCTION,
    sub_agents=[pokemon_agent, assistant_agent],
    generate_content_config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(  # avoid false alarm about rolling dice.
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.OFF,
            ),
        ]
    ),
)


# ADK expects a variable named 'root_agent'
root_agent = root