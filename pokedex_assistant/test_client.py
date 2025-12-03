#!/usr/bin/env python3
"""
Test client for the Pokédx Assistant Agent.
Tests individual functionality using proper A2A communication.
"""

import asyncio
import traceback
from typing import Any
from uuid import uuid4
import httpx

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    SendMessageResponse,
    GetTaskResponse,
    SendMessageSuccessResponse,
    Task,
    TaskState,
    SendMessageRequest,
    MessageSendParams,
    GetTaskRequest,
    TaskQueryParams,
)

def create_send_message_payload(text: str, task_id: str | None = None, context_id: str | None = None) -> dict[str, Any]:
    """Helper function to create the payload for sending a message."""
    payload: dict[str, Any] = {
        "message": {
            "role": "user",
            "parts": [{"kind": "text", "text": text}],
            "messageId": uuid4().hex,
        },
    }

    if task_id:
        payload["message"]["taskId"] = task_id

    if context_id:
        payload["message"]["contextId"] = context_id
    return payload

def print_response_summary(response: Any, description: str, query: str) -> None:
    """Helper function to print a summary of the response."""
    print(f"🧪 {description}: {query}")
    print("-" * 50)
    
    if hasattr(response, "root"):
        if isinstance(response.root, SendMessageSuccessResponse) and isinstance(response.root.result, Task):
            task = response.root.result
            print("✅ Success!")
            print(f"Task ID: {task.id}")
            print(f"Task status: {task.status.state if hasattr(task.status, 'state') else task.status}")
        else:
            print("❌ Unexpected response format")
            print(f"Response: {response.root}")
    else:
        print("❌ Invalid response")
        print(f"Response: {response}")

async def test_assistant_agent():
    """Test the Pokédx Assistant Agent using A2A protocol."""
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
    
    try:
        timeout = httpx.Timeout(60.0)
        async with httpx.AsyncClient(timeout=timeout) as httpx_client:
            # Create a resolver to fetch the agent card
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=agent_url,
            )
            agent_card = await resolver.get_agent_card()
            
            # Create a client to interact with the agent
            client = A2AClient(
                httpx_client=httpx_client,
                agent_card=agent_card,
            )
            
            print("🎓 Testing Pokédx Assistant Agent")
            print("=" * 50)
            
            for i, query in enumerate(test_queries, 1):
                try:
                    # Create and send the message
                    send_message_payload = create_send_message_payload(text=query)
                    request = SendMessageRequest(
                        id=str(uuid4()), params=MessageSendParams(**send_message_payload)
                    )
                    
                    response: SendMessageResponse = await client.send_message(request)
                    print_response_summary(response, f"Test {i}", query)
                    
                    # If we got a task, query it for completion
                    if (isinstance(response.root, SendMessageSuccessResponse) and 
                        isinstance(response.root.result, Task)):
                        task_id = response.root.result.id
                        
                        # Small delay then query task status
                        await asyncio.sleep(3)
                        get_request = GetTaskRequest(id=str(uuid4()), params=TaskQueryParams(id=task_id))
                        get_response: GetTaskResponse = await client.get_task(get_request)
                        
                        if hasattr(get_response, 'root') and hasattr(get_response.root, 'result'):
                            task = get_response.root.result
                            print(f"🔄 Final task status: {task.status.state if hasattr(task.status, 'state') else task.status}")
                            
                            # Try to get response content - check artifacts first
                            if hasattr(task, 'artifacts') and task.artifacts:
                                # Get the response from artifacts
                                for artifact in task.artifacts:
                                    if hasattr(artifact, 'parts') and artifact.parts:
                                        for part in artifact.parts:
                                            # Check for nested text in part.root.text
                                            if hasattr(part, 'root') and hasattr(part.root, 'text'):
                                                content = part.root.text
                                                print(f"🤖 Assistant response: {content[:500]}..." if len(content) > 500 else content)
                                                break
                                            # Check for direct text attribute
                                            elif hasattr(part, 'text'):
                                                content = part.text
                                                print(f"🤖 Assistant response: {content[:500]}..." if len(content) > 500 else content)
                                                break
                                        break
                            elif hasattr(task, 'history') and task.history:
                                # The history should contain the conversation
                                for msg in task.history:
                                    if hasattr(msg, 'role') and msg.role == 'assistant':
                                        if hasattr(msg, 'parts') and msg.parts:
                                            for part in msg.parts:
                                                if hasattr(part, 'text'):
                                                    content = part.text
                                                    print(f"🤖 Assistant response: {content[:500]}..." if len(content) > 500 else content)
                                                    break
                                        break
                            elif hasattr(task, 'result') and task.result:
                                print(f"🤖 Task result: {str(task.result)[:300]}..." if len(str(task.result)) > 300 else str(task.result))
                            elif hasattr(task, 'response') and task.response:
                                print(f"🤖 Task response: {str(task.response)[:300]}..." if len(str(task.response)) > 300 else str(task.response))
                            elif hasattr(task, 'output') and task.output:
                                print(f"🤖 Task output: {str(task.output)[:300]}..." if len(str(task.output)) > 300 else str(task.output))
                            else:
                                print("🤖 Task completed but no response content found")
                    
                    print()
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"❌ Error in test {i}: {e}")
                    print()
            
            print("🏁 Testing complete!")
            
    except Exception as e:
        traceback.print_exc()
        print(f"❌ Failed to connect or test agent: {e}")

async def test_agent_health():
    """Test if the agent is running and healthy."""
    agent_url = "http://localhost:10002"
    
    try:
        timeout = httpx.Timeout(10.0)
        async with httpx.AsyncClient(timeout=timeout) as httpx_client:
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=agent_url,
            )
            agent_card = await resolver.get_agent_card()
            print(f"🟢 Agent is running and accessible")
            print(f"   Agent: {agent_card.name}")
            print(f"   Version: {agent_card.version}")
            print(f"   Skills: {len(agent_card.skills)} available")
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