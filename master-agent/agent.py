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
    name="pokedex_assistant",
    description="An analytical agent specialized in Pokemon comparisons, trivia, and battle analysis",
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